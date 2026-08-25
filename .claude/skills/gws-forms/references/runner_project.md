# The shared runner project

`gws script scripts run` can only execute code that lives inside an Apps Script project **whose Drive file has been manually linked, once, to a standard (non-default) GCP project** in the Apps Script editor UI (Project Settings → Google Cloud Platform (GCP) Project → Change project). There is no REST API field for this association (checked `script.projects.get`/`.create` — no such property exists), so it cannot be automated, and the Apps Script editor itself states the link is **permanent and cannot be reverted**.

Because of that, this skill does **not** create a fresh standalone script project per request. It reuses one pre-linked project as a "form-building runner" and only swaps its `Code.gs` content each time:

- **scriptId**: `11QwsrkXz_oHl3A2iZtjoAlSWmi88w8tLNMKe-GAnTv4JlwmlqvZNP7cq`
- **deploymentId**: `AKfycbzuVcmsZt7U-8jnlsVwIwTBxmDkOYIPNZr1Lwd89vm5UM0KipkwuB3MPax9tp46Tblseg` (entry point: EXECUTION_API, access: MYSELF)
- Linked GCP project number: `24712982711` (the same project the `gws` OAuth client belongs to)
- Drive file name: "gws-forms 스킬 - 공용 폼 생성기 (건드리지 마세요)" — do not rename away from something identifiable, do not delete.

`scripts/deploy_and_run.py` has these two IDs baked in as constants and drives the full push → version → deployment-update → run cycle against them.

## Required auth scopes

The `gws` OAuth token must include `https://www.googleapis.com/auth/forms`, `https://www.googleapis.com/auth/script.projects`, and `https://www.googleapis.com/auth/script.deployments` (check `gws auth status`). If missing: `gws auth login --services calendar,drive,gmail,docs,sheets,slides,tasks,script,forms` (adjust the list to include whatever the account already had — a bare re-login only grants the services you pass, it doesn't preserve the old set).

The Google account must also have "Google Apps Script API" turned on for itself at `script.google.com/home/usersettings` — this is a separate per-account toggle from OAuth scopes, and `script.projects.create`/`update` fail with a distinct 403 message telling you to enable it if it's off.

## If the runner project is ever lost

1. `gws script projects create --json '{"title": "<name>"}'` → note the returned `scriptId`.
2. Push `templates/appsscript.json` + an initial `Code.gs` (any function) into it via `gws script +push --script <scriptId>` (run from the directory containing those two files — `+push`'s `--dir` must be a relative path if used explicitly).
3. `gws script projects versions create --params '{"scriptId": "<scriptId>"}' --json '{"description": "init"}'` → note `versionNumber` (will be 1).
4. `gws script projects deployments create --params '{"scriptId": "<scriptId>"}' --json '{"versionNumber": 1, "manifestFileName": "appsscript"}'` → note `deploymentId`.
5. **Manual, one-time, irreversible step**: open `https://script.google.com/d/<scriptId>/edit` → Project Settings → find the GCP project number tied to the `gws` OAuth client (`gcloud projects describe <project_id> --format="value(projectNumber)"`, where `<project_id>` is whatever `gws auth status` reports) → paste it into "GCP 프로젝트 번호" → confirm. This must be done by hand in a browser; there is no API for it. A human must click through the warning, since it cannot be undone.
6. Update the two constants at the top of `scripts/deploy_and_run.py` and in this file.

Skip straight to step 6's constants if step 1-5 were already done — don't recreate a new runner project just because one exists; reuse it.
