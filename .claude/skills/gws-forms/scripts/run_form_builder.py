#!/usr/bin/env python3
"""Create a Google Form via a persistent Apps Script "builder" project.

Why a persistent project: Apps Script's Execution API (script.scripts.run)
will only execute a project once two one-time, browser-only steps are done
for THAT SPECIFIC project -- see SKILL.md's "One-time setup" section for
why. Redoing those steps for a fresh project on every form would defeat
the point of automation, so this script creates ONE builder project (first
run), pushes assets/Code.gs into it, and reuses it forever after -- every
later call just re-pushes the (identical) code and invokes createForm with
a new spec. Only the first-ever run needs a human/browser in the loop.

Usage:
    python run_form_builder.py ensure
        Create the builder project if it doesn't exist yet, and print
        what's needed to finish one-time setup. Safe to call every time;
        it's a no-op once setup is already complete.

    python run_form_builder.py create --spec content.json
        Push the latest builder code and run createForm(spec) where spec
        is the JSON object in content.json. Prints
        {"formId": ..., "editUrl": ..., "publishedUrl": ...} on success.

The builder project's script ID is cached in gws's own config directory
(next to client_secret.json) so it survives across conversations and
projects -- it's a per-Google-account resource, not a per-repo one.
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"

GWS_CONFIG_DIR = Path(
    os.environ.get("GOOGLE_WORKSPACE_CLI_CONFIG_DIR")
    or (Path.home() / ".config" / "gws")
)
BUILDER_ID_FILE = GWS_CONFIG_DIR / "forms_builder_script_id.txt"
CLIENT_SECRET_FILE = GWS_CONFIG_DIR / "client_secret.json"

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


def push_builder_code(script_id):
    # +push requires a relative --dir, so cd into assets/ first rather than
    # passing ASSETS_DIR's absolute path directly.
    cli_cmd = "cd " + shlex.quote(str(ASSETS_DIR)) + " && npx --yes @googleworkspace/cli script +push --script " + shlex.quote(
        script_id
    ) + " --dir ."
    result = subprocess.run(
        [BASH, "-lc", cli_cmd], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("gws script +push failed")


def gcp_project_number():
    if not CLIENT_SECRET_FILE.exists():
        return None
    data = json.loads(CLIENT_SECRET_FILE.read_text(encoding="utf-8"))
    client_id = (data.get("installed") or data.get("web") or {}).get("client_id", "")
    return client_id.split("-")[0] if "-" in client_id else None


def ensure_builder():
    if BUILDER_ID_FILE.exists():
        script_id = BUILDER_ID_FILE.read_text(encoding="utf-8").strip()
        if script_id:
            push_builder_code(script_id)
            print(json.dumps({"status": "ready", "scriptId": script_id}))
            return script_id

    project = run_gws(
        ["script", "projects", "create", "--json", json.dumps({"title": "gws-forms builder"})]
    )
    script_id = project["scriptId"]
    GWS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    BUILDER_ID_FILE.write_text(script_id, encoding="utf-8")
    push_builder_code(script_id)

    project_number = gcp_project_number()
    print(
        json.dumps(
            {
                "status": "setup_required",
                "scriptId": script_id,
                "message": (
                    "New builder project created. Two one-time browser steps remain "
                    "before it can run -- see SKILL.md's 'One-time setup' section. "
                    "Do NOT retry `create` until these are done, it will fail the same way "
                    "each time until the project is linked."
                ),
                "steps": [
                    {
                        "step": "Enable the Apps Script API for this Google account (skip if already enabled)",
                        "url": "https://script.google.com/home/usersettings",
                    },
                    {
                        "step": "Link this script project's GCP project to the gws CLI's own project",
                        "url": f"https://script.google.com/d/{script_id}/edit",
                        "detail": (
                            f"Open Project Settings (프로젝트 설정) -> Google Cloud Platform (GCP) 프로젝트 "
                            f"-> 프로젝트 변경, and enter GCP project number: {project_number or '<see client_secret.json client_id prefix>'}"
                        ),
                    },
                    {
                        "step": "Authorize the script's own permissions once from the editor",
                        "url": f"https://script.google.com/d/{script_id}/edit",
                        "detail": (
                            "In the editor, select the createForm function and click Run (실행). "
                            "It will fail with a parameter error (spec is undefined) -- that's expected and fine, "
                            "the point is only to click through the '승인 필요' -> '권한 검토' consent screen it triggers."
                        ),
                    },
                ],
            },
            ensure_ascii=False,
        )
    )
    return None


def create(spec_path):
    script_id = ensure_builder()
    if script_id is None:
        raise SystemExit(1)

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    result = run_gws(
        [
            "script",
            "scripts",
            "run",
            "--params",
            json.dumps({"scriptId": script_id}),
            "--json",
            json.dumps({"function": "createForm", "devMode": True, "parameters": [spec]}),
        ]
    )

    if "error" in result:
        sys.stderr.write(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(
            "Apps Script execution failed. If the error mentions permission, storage, "
            "or NOT_FOUND, the one-time setup steps from `ensure` likely aren't complete yet."
        )

    print(json.dumps(result["response"]["result"], ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ensure")
    create_parser = sub.add_parser("create")
    create_parser.add_argument("--spec", required=True, help="Path to the JSON form spec")

    args = parser.parse_args()
    if args.command == "ensure":
        ensure_builder()
    elif args.command == "create":
        create(args.spec)


if __name__ == "__main__":
    main()
