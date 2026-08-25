---
name: gws-forms
description: Builds a Google Form from the user's stated constraints and materials by writing Apps Script (FormApp) code and running it through the gws CLI's Apps Script pipeline (push → version → deploy → run) — not the raw Forms API directly. Use when the user asks to create/generate a Google Form, quiz, survey, or questionnaire from a topic or a list of questions — e.g. "이 조건으로 구글 폼 만들어줘", "설문지 만들어줘", "이 자료로 퀴즈 폼 제작해줘". Do not use for reading/analyzing an existing form's responses (raw `gws forms` REST commands are enough for that).
---

# Gws Forms

## Overview

Turn the user's constraints (title, question list, question types, quiz/grading, etc.) into Apps Script `Code.gs` using `FormApp`, then run it via a shared, pre-linked Apps Script "runner" project so the Apps Script API (`scripts.run`) will actually execute it. See `references/runner_project.md` for why a raw new project can't be spun up per request (Apps Script API execution requires a one-time, irreversible, manual GCP-project link that already exists on the runner project — reuse it, don't recreate it).

Requires `gws auth status` to show `token_valid: true` with the `forms`, `script.projects`, and `script.deployments` scopes, and the account's "Google Apps Script API" personal setting enabled at `script.google.com/home/usersettings`. If either is missing, stop and tell the user what to do (see `references/runner_project.md`) — both require action in an actual browser and can't be done headlessly.

## Workflow

### Step 1: Gather constraints and materials

Ask only for what's missing:
- Form title (and description, if any)
- The question list: for each question — type (short text / paragraph / multiple choice / checkboxes / dropdown / linear scale / grid / date / time / file upload), choices if applicable, required or not
- Quiz mode? If yes, correct answers and points per question
- Any settings: collect respondent email, limit one response per person, custom confirmation message

If the user hands over source material (notes, an outline, an existing document) instead of a literal question list, derive a reasonable question set from it and confirm before building.

### Step 2: Confirm before building

Restate the question list and settings back to the user. This creates a real, persistent Google Form — skip confirmation only if the user's request already specified every question unambiguously.

### Step 3: Write Code.gs

Write a single entry function (pick a clear name, e.g. `buildForm`) using `FormApp`, following the patterns in `references/formapp_cookbook.md`. It must `return` a plain JSON-serializable object — at minimum `{formId, editUrl, publishedUrl}` (see the cookbook's skeleton).

Save it to a scratch directory alongside a copy of `templates/appsscript.json` (static — covers the `forms`/`drive` scopes and `executionApi` config the runner needs; don't rewrite it per request).

### Step 4: Deploy and run

```
python "<skill-dir>/scripts/deploy_and_run.py" --dir <scratch-dir> --function <entryFunctionName>
```

This pushes `Code.gs`/`appsscript.json` into the shared runner project, creates a new version, repoints the runner's existing deployment at it, and executes the function — all against the fixed `scriptId`/`deploymentId` in `references/runner_project.md`. Read the returned `result` object for `formId`/`editUrl`/`publishedUrl`.

If it raises `Script execution failed: ...`, the error detail from Apps Script is in the message — most often a `ReferenceError`/`TypeError` in the generated code (see cookbook's "Common mistakes") rather than an infra problem.

### Step 5: Report and clean up

Tell the user:
- **편집**: the `editUrl` (opens the form in the Forms editor)
- **응답 링크**: the `publishedUrl` (what to share with respondents)

Delete the scratch `Code.gs`/`appsscript.json` directory. The created Form itself is a normal, independent Drive file — it is not affected by later runs of this skill (only the shared runner project's code gets overwritten each time, not any form it already created).

## Notes

- The runner project executes one request at a time (pushing new code overwrites the previous run's code before that run's version is even referenced again, but each run's version/deployment-update/run sequence completes fully before the next starts) — don't fire concurrent `gws-forms` invocations against it.
- Never invent quiz answers, point values, or question content beyond what the user gave you or what you can reasonably derive from their material — ask rather than guess for anything graded.
- `+push` replaces **all** files in the target project — never push a scratch dir that has extra unrelated files sitting in it.
