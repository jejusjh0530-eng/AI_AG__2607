#!/usr/bin/env python3
"""Push Code.gs to the shared gws-forms runner project, redeploy it, and run it.

This wraps the exact 4-call gws CLI sequence required to make freshly-pushed
Apps Script code actually executable via the Apps Script API:
  1. gws script +push            (upload Code.gs / appsscript.json)
  2. gws script projects versions create   (snapshot the new code as a version)
  3. gws script projects deployments update (point the existing deployment at that version)
  4. gws script scripts run       (execute the function, using the deployment ID)

Steps 2-4 need each other's output (new version number -> deployment update ->
same deployment ID used as the scriptId for run), which is easy to get wrong
by hand -- that's why this is a script and not inline shell commands.

Usage:
    python deploy_and_run.py --dir <folder with Code.gs + appsscript.json> --function <entryFunctionName>

The runner project's scriptId/deploymentId are fixed constants below -- see
references/runner_project.md for what they are and how to recreate them if
this project is ever lost.
"""
import argparse
import json
import shutil
import subprocess
import sys

RUNNER_SCRIPT_ID = "11QwsrkXz_oHl3A2iZtjoAlSWmi88w8tLNMKe-GAnTv4JlwmlqvZNP7cq"
RUNNER_DEPLOYMENT_ID = "AKfycbzuVcmsZt7U-8jnlsVwIwTBxmDkOYIPNZr1Lwd89vm5UM0KipkwuB3MPax9tp46Tblseg"

# shutil.which resolves the platform-correct executable (e.g. gws.cmd on
# Windows) -- plain "gws" fails under subprocess without shell=True there.
GWS_BIN = shutil.which("gws") or "gws"


def run_gws(args, cwd=None):
    proc = subprocess.run(
        [GWS_BIN] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"gws {' '.join(args)} failed (exit {proc.returncode})")
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Folder containing Code.gs and appsscript.json")
    parser.add_argument("--function", required=True, help="Entry function name to execute")
    parser.add_argument("--params", default="[]", help="JSON array of parameters to pass to the function")
    args = parser.parse_args()

    print("1/4 pushing code...", file=sys.stderr)
    run_gws(["script", "+push", "--script", RUNNER_SCRIPT_ID], cwd=args.dir)

    print("2/4 creating version...", file=sys.stderr)
    version = run_gws([
        "script", "projects", "versions", "create",
        "--params", json.dumps({"scriptId": RUNNER_SCRIPT_ID}),
        "--json", json.dumps({"description": "gws-forms skill run"}),
    ])
    version_number = version["versionNumber"]

    print(f"3/4 pointing deployment at version {version_number}...", file=sys.stderr)
    run_gws([
        "script", "projects", "deployments", "update",
        "--params", json.dumps({"scriptId": RUNNER_SCRIPT_ID, "deploymentId": RUNNER_DEPLOYMENT_ID}),
        "--json", json.dumps({"deploymentConfig": {
            "versionNumber": version_number,
            "manifestFileName": "appsscript",
            "description": "gws-forms skill run",
        }}),
    ])

    print("4/4 running...", file=sys.stderr)
    result = run_gws([
        "script", "scripts", "run",
        "--params", json.dumps({"scriptId": RUNNER_DEPLOYMENT_ID}),
        "--json", json.dumps({"function": args.function, "parameters": json.loads(args.params)}),
    ])

    if "error" in result:
        raise SystemExit(f"Script execution failed: {json.dumps(result['error'], ensure_ascii=False)}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
