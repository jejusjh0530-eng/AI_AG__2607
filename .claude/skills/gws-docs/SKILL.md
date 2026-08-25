---
name: gws-docs
description: Given a topic, researches it and writes it up directly into a new Google Doc using the gws CLI (docs.documents create/batchUpdate — no python-docx, no local .docx file). Use when the user asks to write a document on a topic and put it in Google Docs, says "이 주제로 구글 독스에 문서 작성해줘", "gws로 구글 문서 만들어줘", "Google Docs에 정리해줘", or otherwise asks for a Docs (not Word/.docx) deliverable. Do not use for local .docx output (use docx-research-report) or for topics that don't need research (use gws docs +write directly for a quick one-line append).
---

# Gws Docs

## Overview

Take a topic from the user, research it, and write the result straight into a new Google Doc via the `gws` CLI (`docs.documents.create` + `docs.documents.batchUpdate`). Requires `gws` to be installed and authenticated (`gws auth status` — must show `token_valid: true` and the `documents` scope).

## Workflow

### Step 1: Confirm scope

Ask only for what's missing:
- Topic
- Document title (default: the topic itself)
- Any section structure the user wants; otherwise decide a reasonable structure (overview, key points, details, sources)

### Step 2: Research

Use WebSearch/WebFetch to gather current, accurate information on the topic. Group findings into logical sections. Keep track of the URLs used — add a "출처" (Sources) section listing them. Never fabricate facts; if a claim can't be sourced, omit it.

### Step 3: Write the content JSON

Build a JSON file matching `references/content_schema.md`. Save it to a scratch path, e.g. `<topic-slug>_content.json`.

### Step 4: Create the empty Google Doc

```
gws docs documents create --json '{"title": "<Document Title>"}'
```

Read `documentId` from the response — every following step needs it.

### Step 5: Generate the batchUpdate requests

```
python "<skill-dir>/scripts/build_batch_requests.py" --input <topic-slug>_content.json --output <topic-slug>_requests.json
```

This computes the Docs API's character-offset indices for you (see `references/content_schema.md` for why that has to be scripted, not hand-written).

### Step 6: Apply the requests to the document

```
gws docs documents batchUpdate --params '{"documentId": "<documentId>"}' --json "$(cat <topic-slug>_requests.json)"
```

On Windows PowerShell, read the file into a variable first (`Get-Content ... -Raw`) instead of `$(cat ...)`.

### Step 7: Clean up and deliver

Delete the intermediate `_content.json` and `_requests.json` scratch files. Report the document's URL to the user:
`https://docs.google.com/document/d/<documentId>/edit`

## Notes

- `documents.create` only accepts `title` — content must always go in via a separate `batchUpdate` (Step 6).
- For a trivial one-off append to an *existing* doc with no formatting needs, skip this whole workflow and just run `gws docs +write --document <ID> --text '...'` directly.
- If `gws auth status` shows the `documents` scope missing or `token_valid: false`, stop and tell the user to run `gws auth login` before continuing.
