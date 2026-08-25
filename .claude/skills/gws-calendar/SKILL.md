---
name: gws-calendar
description: Registers a Google Calendar event exactly as the user directs, using the gws CLI (calendar +insert helper, or raw events.insert for all-day/recurring/reminder cases). Use when the user asks to add, book, or schedule something on their calendar — e.g. "이 일정 캘린더에 등록해줘", "내일 오후 3시에 회의 잡아줘", "다음 주 화요일 종일 일정 추가해줘", "이 일정 반복으로 등록해줘". This is a write skill — do not use it for read-only briefings or "이번 주 일정 알려줘" (use the schedule-manager/일정 관리 agent for those).
---

# Gws Calendar

## Overview

Turn a natural-language scheduling request into a Google Calendar event via the `gws` CLI. Requires `gws` to be installed and authenticated (`gws auth status` — must show `token_valid: true` and the `calendar` scope).

Creating an event is a **visible, hard-to-fully-undo action** — it can email invites to attendees and clutters a shared calendar. Always restate the parsed details back to the user and get confirmation before calling `gws`, unless the user's own message already gave every detail explicitly and unambiguously (exact date, time, title).

## Workflow

### Step 1: Extract event details from the request

Pull out, in order of importance:
- **Title/summary** (required)
- **Start date/time** (required) — resolve relative dates ("내일", "다음 주 화요일") against the current date. If the user gives a date but no time, treat it as an **all-day event** (Step 3b), not a timed one.
- **End date/time** — if omitted for a timed event, default to **1 hour** after start. For an all-day event, default to the same single day.
- **Calendar** — default to `primary`. If the user names a specific calendar (e.g. "수업 캘린더에", "학원 일정에"), resolve it: `gws calendar calendarList list --params '{"maxResults": 50}'` and match by `summary`.
- **Location, description, attendees (emails), Google Meet link** — only if mentioned.
- **Recurrence / reminders** — only if mentioned (Step 3b).

Use **RFC3339 with an explicit UTC offset** for all timed values, e.g. `2026-08-22T15:00:00+09:00`. Default to `+09:00` (Asia/Seoul) unless the target calendar's `timeZone` (from `calendarList`) says otherwise or the user specifies a different zone.

### Step 2: Confirm with the user

Restate: title, date/time (or "종일"/all-day), calendar, and any attendees/location. Skip this only when the user's request already unambiguously specified every field being used.

### Step 3a: Simple timed event → use the `+insert` helper

```
gws calendar +insert --summary '<title>' --start '<RFC3339>' --end '<RFC3339>' \
  [--calendar <calendarId>] [--location '<text>'] [--description '<text>'] \
  [--attendee <email>] [--attendee <email2>] [--meet]
```

`--attendee` can repeat. `--meet` attaches a Google Meet link. This covers the large majority of requests.

### Step 3b: All-day, recurring, or reminder-customized event → raw `events.insert`

`+insert` cannot express all-day dates, recurrence rules, or custom reminders. Build the request body per `references/event_json.md` and send it directly:

```
gws calendar events insert --params '{"calendarId": "<calendarId or primary>"}' --json '<event JSON>'
```

### Step 4: Report the result

From the response, tell the user the event was created and give the `htmlLink` so they can open it directly in Google Calendar. If attendees were added, mention that invites were sent.

### Step 5: Editing or cancelling afterward

Reuse the `id` returned from `insert`:
- Update: `gws calendar events patch --params '{"calendarId": "<id>", "eventId": "<eventId>"}' --json '{...fields to change...}'`
- Delete: `gws calendar events delete --params '{"calendarId": "<id>", "eventId": "<eventId>"}' -o <scratch-dir>/delete.html`

`events delete` returns an empty response, and `gws` writes that as a `download.html` file in the current directory if `-o` is omitted — always pass `-o` pointing at a scratch path so it doesn't litter the project directory.

## Notes

- If `gws auth status` shows the `calendar` scope missing or `token_valid: false`, stop and tell the user to run `gws auth login` before continuing.
- Never invent attendee emails or a location that wasn't given — leave those fields out entirely rather than guessing.
- Adding `--attendee` sends that person a real invite email. Always confirm the attendee list with the user before running the command (per Step 2) — this isn't a locally-reversible action. For explicit control over whether/who gets emailed, use the raw form with `sendUpdates` (see `references/event_json.md`).
