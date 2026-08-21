#!/usr/bin/env python3
"""Create a Google Doc via the gws CLI from a simple block-based content spec.

The Google Docs API only accepts structural edits as index-based
batchUpdate requests (insertText, updateParagraphStyle,
createParagraphBullets, ...), and every index shifts as soon as any text
is inserted. Computing those ranges by hand is slow and error-prone, so
this script does it once: it inserts all the document's text in a single
call and derives every style/bullet range from the offsets it tracked
while building that text, which keeps the math simple and correct.

Usage:
    python create_google_doc.py --title "TITLE" --content content.json

content.json is a JSON array of blocks, each one of:
    {"type": "heading1", "text": "..."}
    {"type": "heading2", "text": "..."}
    {"type": "heading3", "text": "..."}
    {"type": "paragraph", "text": "..."}
    {"type": "bullet", "text": "..."}

Consecutive "bullet" blocks are grouped into a single bulleted list.

Prints a JSON object with the new document's id and edit URL:
    {"documentId": "...", "url": "https://docs.google.com/document/d/.../edit"}
"""
import argparse
import json
import shlex
import shutil
import subprocess
import sys

HEADING_STYLES = {
    "heading1": "HEADING_1",
    "heading2": "HEADING_2",
    "heading3": "HEADING_3",
}

# On Windows, npx resolves to npx.cmd, which Win32 CreateProcess cannot launch
# directly (shell=False) and which mangles JSON-with-quotes arguments when run
# through cmd.exe (shell=True). Routing through bash's POSIX quoting -- the
# same shell every gws call in this project already goes through -- sidesteps
# both problems and works unchanged on macOS/Linux where bash is just bash.
BASH = shutil.which("bash") or r"C:\Program Files\Git\usr\bin\bash.exe"


def run_gws(args):
    cli_cmd = "npx --yes @googleworkspace/cli " + " ".join(shlex.quote(a) for a in args)
    result = subprocess.run(
        [BASH, "-lc", cli_cmd], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"gws command failed: {' '.join(args)}")
    return json.loads(result.stdout)


def build_requests(blocks):
    """Insert all text in one shot, then style each block by the offsets
    recorded while concatenating it -- avoids the classic Docs API trap of
    inserting paragraph-by-paragraph and having every later index go stale."""
    text_parts = []
    ranges = []  # (start, end, block) -- end excludes the trailing newline
    offset = 1  # document body content starts at index 1
    for block in blocks:
        block_text = block["text"].rstrip("\n") + "\n"
        start = offset
        end = start + len(block_text) - 1
        ranges.append((start, end, block))
        text_parts.append(block_text)
        offset += len(block_text)

    full_text = "".join(text_parts)
    requests = [{"insertText": {"location": {"index": 1}, "text": full_text}}]

    bullet_run_start = None
    bullet_run_end = None

    def flush_bullets():
        nonlocal bullet_run_start, bullet_run_end
        if bullet_run_start is not None:
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": bullet_run_start, "endIndex": bullet_run_end},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })
            bullet_run_start = None
            bullet_run_end = None

    for start, end, block in ranges:
        btype = block["type"]
        if btype in HEADING_STYLES:
            flush_bullets()
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": HEADING_STYLES[btype]},
                    "fields": "namedStyleType",
                }
            })
        elif btype == "bullet":
            if bullet_run_start is None:
                bullet_run_start = start
            bullet_run_end = end
        else:
            flush_bullets()
    flush_bullets()

    return requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Title of the new Google Doc")
    parser.add_argument("--content", required=True, help="Path to the JSON content spec")
    args = parser.parse_args()

    with open(args.content, encoding="utf-8") as f:
        blocks = json.load(f)

    doc = run_gws(["docs", "documents", "create", "--json", json.dumps({"title": args.title})])
    document_id = doc["documentId"]

    requests = build_requests(blocks)
    run_gws([
        "docs", "documents", "batchUpdate",
        "--params", json.dumps({"documentId": document_id}),
        "--json", json.dumps({"requests": requests}),
    ])

    url = f"https://docs.google.com/document/d/{document_id}/edit"
    print(json.dumps({"documentId": document_id, "url": url}, ensure_ascii=False))


if __name__ == "__main__":
    main()
