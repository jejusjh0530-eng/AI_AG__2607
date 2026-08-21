---
name: gws-docs
description: Writes a Google Docs document (not a local .docx/Word file) on a given topic, using the authenticated gws CLI to create the doc directly in the user's Google Drive. Covers both cases — researching a topic from scratch via web search, and formatting/organizing content the user already provided (pasted text, notes from earlier in the conversation, a local file) — into a structured Google Doc with proper headings and bullet lists. Use this skill whenever the user asks to write, draft, or organize something specifically as a "구글 문서"/"Google Docs"/"구글독스" document, or says things like "이 내용 구글 문서로 정리해줘", "~에 대해 조사해서 구글독스로 만들어줘", "make a Google Doc about X", even if they don't mention gws or the CLI by name. Do NOT use this for requests that want a local Word (.docx) file (use research-report-docx for that) or an Excel file (use research-report-xlsx) — the distinguishing signal is that the user wants it living in Google Docs / Google Drive, editable and shareable there, not saved as a local file.
---

# gws-docs

## What this skill does

Creates a real Google Docs document — not a local file — directly in the
user's Google Drive, using the `gws` CLI (Google Workspace CLI) that this
project already has authenticated. It handles both of the situations that
come up when someone asks for "a Google Doc about X":

- **From scratch**: the user names a topic and nothing else. Research it
  the same way you would for any report, then write the findings into the
  new doc.
- **From existing material**: the user already has the content — pasted
  text, notes earlier in the conversation, a local file — and just wants
  it turned into a properly structured Google Doc. Skip research; organize
  what's already there.

Either way, the deliverable is a link to a live Google Doc the user can
open, edit, and share from their own Drive — not an attachment.

## Before you start: check gws authentication

The Docs API needs the `documents` scope (and `drive`/`drive.file` so the
CLI can create the file), which is broader than the scopes a `gws`
connection set up for something else — like Gmail-only — would have. Run:

```bash
npx --yes @googleworkspace/cli auth status
```

and check `"scopes"` for `https://www.googleapis.com/auth/documents`. If
it's missing, the create step below will fail with an auth error (exit
code 2), not a helpful message, so it's worth checking first. To add the
scope:

```bash
npx --yes @googleworkspace/cli auth login --services docs,drive,gmail,calendar,forms
```

This opens a browser consent URL. If a browser-automation tool (e.g.
Playwright MCP) is available in the current session, you can drive the
consent flow yourself; otherwise share the URL and ask the user to
complete it, the same way any other `gws auth login` is handled in this
project. Requesting the other already-used services (`gmail`, `calendar`,
`forms`) alongside `docs`/`drive` in the same login keeps this as a single
combined token instead of silently dropping scopes the user granted
earlier.

## Workflow

1. **Decide: research or organize?** If the user gave you a bare topic
   with no supporting material, research it with `WebSearch` (and
   `WebFetch` for promising sources) the way you would for any report —
   gather enough to support a few real sections, not just one paragraph,
   and keep track of source URLs for a "출처"/"Sources" section at the
   end. If the user already handed you the content, skip straight to
   structuring it — re-researching material they already gave you wastes
   their time and risks contradicting what they actually said.

2. **Shape the content into blocks.** The Docs API only understands
   position-indexed edits, not markdown, so this skill's bundled script
   takes a simple block list instead. Write it to a scratch JSON file:

   ```json
   [
     {"type": "heading1", "text": "Document Title"},
     {"type": "paragraph", "text": "Opening paragraph..."},
     {"type": "heading2", "text": "Section Name"},
     {"type": "paragraph", "text": "..."},
     {"type": "bullet", "text": "First point"},
     {"type": "bullet", "text": "Second point"},
     {"type": "heading2", "text": "Sources"},
     {"type": "bullet", "text": "https://..."}
   ]
   ```

   Valid `type`s: `heading1`, `heading2`, `heading3`, `paragraph`,
   `bullet`. Consecutive `bullet` blocks automatically become one bulleted
   list — you don't need to group them yourself. Shape the number and
   names of sections to fit the topic; there's no fixed template. A
   `heading1` block as the first entry gives the doc a visible title
   inside the body (separate from the Drive filename, which comes from
   `--title` in the next step).

3. **Create the doc.** Run the bundled script, which creates a blank
   Google Doc via `gws docs documents create` and then applies all the
   text/heading/bullet formatting in one `batchUpdate` call:

   ```bash
   python "<skill-dir>/scripts/create_google_doc.py" --title "Doc Title" --content blocks.json
   ```

   It prints `{"documentId": "...", "url": "https://docs.google.com/document/d/.../edit"}`.
   The doc lands in the user's Drive root (My Drive) — this skill doesn't
   move it into a folder or change its sharing settings; if the user wants
   either, that's a separate, explicit step, since changing permissions on
   something is not a default you want to guess into.

4. **Hand back the link.** Give the user the `url` from the script output
   and a one- or two-line summary of what the doc covers (and, if you
   researched it, which sources you drew from) so they can sanity-check it
   before relying on the content.

## Why a bundled script instead of raw batchUpdate calls

Google Docs' `batchUpdate` requests (`insertText`, `updateParagraphStyle`,
`createParagraphBullets`, ...) all address the document by character
index, and every index downstream of an edit shifts as soon as that edit
is applied. Hand-building this — especially across several
`insertText` calls — is exactly the kind of fiddly, easy-to-get-wrong
bookkeeping a script should own instead of redoing by hand each time.
`scripts/create_google_doc.py` sidesteps the shifting-index problem
entirely by inserting the full document text in a *single* `insertText`
call and computing every style/bullet range from the offsets it tracked
while assembling that text — so the ranges are correct by construction,
not by careful counting.

The script shells out to the same `gws` CLI you'd otherwise call
directly (`docs documents create`, `docs documents batchUpdate`), it just
handles the request-building. If you need something the block schema
doesn't cover (tables, images, links, text color), fall back to calling
`gws docs documents batchUpdate` yourself with the additional request
types — see `gws schema docs.documents.batchUpdate --resolve-refs` for
the full request shape.

## Notes

- The script shells commands through `bash` explicitly (not the platform
  default shell) so that JSON payloads containing quotes and non-ASCII
  text pass through unmangled — this matters on Windows, where `npx`
  resolves to a `.cmd` file that neither direct `CreateProcess` nor
  `cmd.exe` handles cleanly for that kind of argument. This is transparent
  to you as the caller; just run the script as shown above.
- If `gws auth status` shows the `documents`/`drive` scopes are present
  but a call still fails with an auth error, the token may have been
  issued for a narrower scope set before this skill's requirements were
  known — re-run the `auth login` command from the top of this file with
  the full service list.
- If web search isn't available in the current environment for the
  research path, say so explicitly and offer to write the doc from
  existing knowledge instead, noting it may not reflect the latest
  information.
