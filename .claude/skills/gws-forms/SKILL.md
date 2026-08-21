---
name: gws-forms
description: Builds a Google Form (not a local file, not a Google Docs questionnaire) from constraints and material the user provides — a topic, a list of questions, survey requirements, quiz content, RSVP/registration fields, etc. — using the authenticated gws CLI to drive Google Apps Script's FormApp service, which supports far richer item types (multiple choice, checkboxes, dropdowns, linear scale, date/time, sections, quizzes with graded answers) than the raw Forms REST API alone. Use this whenever the user asks to create, build, or set up a Google Form, survey, questionnaire, quiz, or RSVP form (e.g. "설문지 만들어줘", "구글 폼으로 신청서 만들어줘", "이 질문들로 퀴즈 폼 만들어줘", "make a Google Form for X"), even if they don't mention gws, Apps Script, or the exact item types by name. Do NOT use this for a Google Doc or Sheet (use gws-docs or plain gws sheets calls for those) — this skill is specifically for the Forms product.
---

# gws-forms

## What this skill does

Builds a real Google Form in the user's Google Drive from whatever
constraints and material they give you — a topic to write questions
about, a list of questions they already have, quiz content with correct
answers, registration/RSVP fields, and so on.

It builds forms through **Google Apps Script's `FormApp` service**
rather than calling the Forms REST API's `forms.body` methods directly.
`FormApp` is the officially-supported, much richer way to assemble a form
in one shot — it covers item types and settings (linear scale, date/time
items, section/page breaks, quiz grading with per-choice correctness)
that are awkward or unsupported through raw API requests. The tradeoff is
that running Apps Script through the API needs a one-time setup that raw
API calls don't — see below — but that cost is paid once per Google
account, not once per form.

## One-time setup

This setup is per Google account, not per form. Once it's done, every
future `gws-forms` request in this project (or any other project using
the same authenticated account) just works — skip straight to "Building a
form" below. But the first time through, three things have to happen
before Apps Script's Execution API will run anything at all, and each one
fails in a *different*, non-obvious way if skipped:

1. **Confirm `gws` auth has the right scopes.** Run
   `npx --yes @googleworkspace/cli auth status` and check for
   `https://www.googleapis.com/auth/script.projects` and
   `https://www.googleapis.com/auth/forms` in `"scopes"`. If missing, run
   `npx --yes @googleworkspace/cli auth login --scopes "<existing scopes>,https://www.googleapis.com/auth/script.projects,https://www.googleapis.com/auth/forms"`
   — pass the account's *current* scopes plus these two, not just
   `--services script`, which pulls in a much broader set (admin
   directory, full Gmail, spreadsheets, groups) that this skill doesn't
   need and shouldn't request.

2. **Run `python "<skill-dir>/scripts/run_form_builder.py" ensure`.**
   First time, this creates one persistent "gws-forms builder" Apps
   Script project, pushes `assets/Code.gs` into it, and prints a
   `setup_required` block naming three things that still have to happen
   in a browser before it can execute — each is a real, separate failure
   mode if skipped, confirmed by hitting every one of them while building
   this skill:

   - **Enable the Apps Script API** for the account at
     `https://script.google.com/home/usersettings` (a per-account toggle,
     separate from any OAuth scope). Skipping this makes every
     `script.projects.create` call fail outright with a 403 telling you
     exactly this.
   - **Link the builder project's GCP project.** Open
     `https://script.google.com/d/<scriptId>/edit` → 프로젝트 설정
     (Project Settings) → Google Cloud Platform(GCP) 프로젝트 → 프로젝트
     변경, and enter the GCP project *number* (not project ID string) of
     the gws CLI's own OAuth client — it's the numeric prefix of the
     client ID in `client_secret.json` (e.g. `828697162831` from
     `828697162831-xxxx.apps.googleusercontent.com`); `run_form_builder.py
     ensure`'s output includes this number already extracted. A
     freshly-created Apps Script project defaults to an internal "기본값"
     (default) GCP project that the Execution API silently can't
     authorize against — calls fail with `"a server error occurred while
     reading from storage. Error code NOT_FOUND"`, which reads like a
     transient outage but isn't; it's this exact missing link, every
     time.
   - **Authorize the script's own permissions once.** In the same editor,
     select the `createForm` function and click 실행 (Run). It throws a
     parameter error immediately (`spec` is undefined) — that's expected,
     the run is only there to trigger the "승인 필요" (authorization
     required) dialog → 권한 검토 (review permissions) → 계속 (continue)
     consent flow for the script project itself. Without this, calls fail
     with a `403 The caller does not have permission` even though the
     GCP project is linked and the gws OAuth token has every scope it
     needs — the script project has its *own*, separate authorization
     independent of the calling tool's OAuth grant.

   If a browser-automation tool (e.g. Playwright MCP) is available in the
   session, drive all three steps yourself the same way any other `gws
   auth login` browser step in this project gets handled; otherwise walk
   the user through them with the exact URLs from the `ensure` output.

3. **Re-run `ensure`** once those three are done — it pushes the latest
   `Code.gs` (cheap, idempotent, safe to call before every form too) and
   should print `{"status": "ready", ...}`.

## Building a form

1. **Turn the user's request into a content spec.** Whether they gave you
   a bare topic ("설문지 하나 만들어줘, 만족도 조사용") or a full list of
   questions, shape it into the JSON schema `assets/Code.gs`'s
   `createForm` expects — see the schema documented in that file's
   header comment. In short: a `title`, optional `description`, and an
   ordered `items` array where each item has a `type` (`text`,
   `paragraph`, `multiple_choice`, `checkbox`, `dropdown`, `scale`,
   `date`, `time`, or `section`) plus `title` and type-specific fields
   (`choices` for the choice types, `lower`/`upper` for `scale`, etc.).
   For a quiz, set `spec.isQuiz: true` and give `correctAnswers` (and
   optionally `points`) on the graded items.

   Write this spec to a scratch JSON file.

2. **Run:**

   ```bash
   python "<skill-dir>/scripts/run_form_builder.py" create --spec content.json
   ```

   This re-pushes the builder code (in case it changed) and invokes
   `createForm(spec)` through the Apps Script Execution API on the
   persistent builder project — no new script project per form, which is
   exactly what makes this fast after the one-time setup above. On
   success it prints `{"formId", "editUrl", "publishedUrl"}`.

3. **Hand back both links** — `editUrl` for the user to review/adjust
   questions, `publishedUrl` for whoever will actually fill it out — and
   a one-line summary of what the form covers, so the user can
   sanity-check it before sharing it further.

## Extending the item schema

If a request needs something `assets/Code.gs`'s schema doesn't cover yet
(file upload items, image/video items, branching page navigation), add
a case to the `switch` in `createForm` using the corresponding `FormApp`
method (`addFileUploadItem`, `addImageItem`, `setGoToPage`, ...) — the
[Apps Script FormApp reference](https://developers.google.com/apps-script/reference/forms/form-app)
covers the full surface. Keep the spec schema additive (new optional
fields) so existing specs and the builder project itself don't need to
change shape.

## Notes

- `run_form_builder.py`'s `gws` calls go through `bash -lc` explicitly
  (not the platform default shell), for the same reason `gws-docs`'s
  script does: on Windows, `npx` resolves to a `.cmd` file that neither
  `CreateProcess` nor `cmd.exe` handles cleanly for JSON-with-quotes
  arguments. This is transparent to you as the caller.
- Pass `--json` to `gws script scripts run` as a **single-line** JSON
  string. A pretty-printed, multi-line `--json` value fails with `Invalid
  --json body: EOF while parsing an object` — `run_form_builder.py`
  already does this correctly via `json.dumps` (which doesn't insert
  newlines by default); just don't hand-format the spec file with
  embedded literal newlines inside a shell arg if you ever call `gws`
  directly instead of through the script.
- The builder project's script ID is cached at
  `<gws config dir>/forms_builder_script_id.txt` (next to
  `client_secret.json`) — an account-level resource, not something to
  commit to this repo or duplicate per project.
- If a `create` call fails with a permission, storage, or `NOT_FOUND`
  error after setup was supposedly done, walk through the three one-time
  steps again for the builder project specifically — it's easy to
  complete them for a throwaway test project while validating this skill
  and then create the *real* builder project fresh without repeating them.
