---
name: gws-gmail
description: Drafts an email from the user's request using the gws CLI, shows the full draft for review, and only sends it after the user explicitly approves — never sends automatically. Use when the user asks to write/send an email, draft a message to someone, or reply/forward via Gmail — e.g. "이 내용으로 메일 초안 작성해줘", "이 사람한테 메일 보내줘", "이 메일 답장 초안 써줘". Sending is always gated on explicit user approval, even if the request sounds like "그냥 보내줘" — read Step 3 before skipping confirmation.
---

# Gws Gmail

## Overview

Turn the user's request into a Gmail **draft** first (never a directly-sent message), show it back to them, and only call the send command after they explicitly say to send it. Requires `gws` authenticated with the `gmail.modify` scope (`gws auth status`) — this is already covered by the account's current grant, no re-auth needed.

## Workflow

### Step 1: Gather what's needed

Ask only for what's missing:
- Recipient(s) (To — required), Cc/Bcc if any
- Subject
- Purpose/key points to cover, and tone if it matters (formal/casual)
- Attachments, if any (local file paths)

If the user gives you source material instead of exact wording (e.g. "이 내용 요약해서 보내줘"), draft reasonable prose from it — don't ask them to write the email themselves.

For a reply/forward, you need the target message's Gmail ID. If the user doesn't supply it, find it with `gws gmail +triage` (unread inbox summary) or `gws gmail users messages list --params '{"userId": "me", "q": "<search terms>"}'`, confirm you found the right message, then proceed.

### Step 2: Create the draft

All three helpers support `--draft` — always include it here, regardless of which one applies:

```
# New email
gws gmail +send --to <emails> --subject '<subject>' --body '<text>' --draft \
  [--cc <emails>] [--bcc <emails>] [--html] [-a <path> ...] [--from <alias-email>]

# Reply (auto-threads via In-Reply-To/References, quotes the original)
gws gmail +reply --message-id <id> --body '<text>' --draft \
  [--to <extra-emails>] [--cc <emails>] [--bcc <emails>] [--html] [-a <path> ...]
# or +reply-all for reply-all

# Forward (includes the original message + its attachments by default)
gws gmail +forward --message-id <id> --to <emails> --draft \
  [--body '<note>'] [--cc <emails>] [--bcc <emails>] [--html] [-a <path> ...] [--no-original-attachments]
```

`--html` treats `--body` as an HTML fragment (`<p>`, `<b>`, `<a>`, `<br>`, etc. — no `<html>`/`<body>` wrapper). Omit it for plain text. These handle MIME/base64 encoding, quoting, threading headers, and attachments (25MB total) automatically — never hand-build a `raw` message.

Save the returned `id` (the draft ID, e.g. `"id": "r1234567890"`) — Step 4 needs it.

### Step 3: Show the draft and get explicit approval

Restate the full draft in chat: To/Cc/Bcc, Subject, and the body. Ask the user to confirm before sending.

**Always do this, even if the original request already said "보내줘"/"전송해줘".** A created draft is cheap to fix; a sent email is not — treat "approval to write this email" and "approval to send it" as two separate confirmations, and get both.

If the user asks for changes: delete the draft (`gws gmail users drafts delete --params '{"userId": "me", "id": "<draftId>"}'`) and create a new one via Step 2 with the revised content, then show it again. Don't try to hand-edit an existing draft's MIME content.

### Step 4: Send only on explicit approval

```
gws gmail users drafts send --params '{"userId": "me"}' --json '{"id": "<draftId>"}'
```

Report the result (confirm it sent) to the user.

### If the user declines

Delete the draft so it doesn't linger in their Drafts folder:
```
gws gmail users drafts delete --params '{"userId": "me", "id": "<draftId>"}'
```

## Notes

- Never invent recipient addresses, facts, or claims not given by the user or clearly derivable from material they provided.
- Any of `+send`/`+reply`/`+reply-all`/`+forward` without `--draft` sends immediately — the whole point of this skill is to never call them that way. Always include `--draft` in Step 2.
