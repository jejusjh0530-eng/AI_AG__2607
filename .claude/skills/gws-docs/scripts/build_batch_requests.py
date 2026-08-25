#!/usr/bin/env python3
"""Turn a structured content JSON into a Google Docs batchUpdate requests JSON.

Usage:
    python build_batch_requests.py --input content.json --output requests.json

Input schema (see references/content_schema.md):
{
  "heading": "Document Title",
  "sections": [
    {"heading": "Section Title", "body": "Paragraph text.\nSecond paragraph."},
    {"heading": "Another Section", "bullets": ["Point one", "Point two"]}
  ]
}

The script computes Google Docs API insertion indices itself (the Docs API
requires precise character offsets, and getting them wrong corrupts the
document), so callers only need to provide plain text.
"""
import argparse
import json


def build_requests(content):
    requests = []
    index = 1  # Docs body always starts at index 1

    def insert_block(text, style, bullet=False):
        nonlocal index
        text = text if text.endswith("\n") else text + "\n"
        requests.append({
            "insertText": {"location": {"index": index}, "text": text}
        })
        start = index
        end = index + len(text) - 1  # exclude trailing newline from paragraph range
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end + 1},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType",
            }
        })
        if bullet:
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start, "endIndex": end + 1},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })
        index += len(text)

    if content.get("heading"):
        insert_block(content["heading"], "TITLE")

    for section in content.get("sections", []):
        if section.get("heading"):
            insert_block(section["heading"], "HEADING_1")
        if section.get("body"):
            for para in section["body"].split("\n"):
                if para.strip():
                    insert_block(para, "NORMAL_TEXT")
        for bullet_text in section.get("bullets", []):
            insert_block(bullet_text, "NORMAL_TEXT", bullet=True)

    return {"requests": requests}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        content = json.load(f)

    result = build_requests(content)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(result['requests'])} requests to {args.output}")


if __name__ == "__main__":
    main()
