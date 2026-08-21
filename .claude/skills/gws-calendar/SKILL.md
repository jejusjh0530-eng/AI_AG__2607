---
name: gws-calendar
description: Creates, updates, and cancels/deletes events on the user's Google Calendar using the authenticated gws CLI. This is the write counterpart to the read-only "일정관리" weekly-briefing subagent — use this skill whenever the user wants to actually change their calendar, not just see it. Trigger on requests like "일정 등록해줘", "캘린더에 추가해줘", "다음주 금요일 3시에 미팅 잡아줘", "그 일정 시간 바꿔줘", "그거 취소해줘"/"삭제해줘", "schedule a call with X on Tuesday", even if the user doesn't mention gws or "calendar" by name — a request to book/move/cancel something at a specific time is calendar work. Do NOT use this for read-only requests ("이번주 일정 보여줘", "다음주 스케줄 알려줘") — route those to the 일정관리 subagent instead, since this skill's job is writing, not reporting.
---

# gws-calendar

## What this skill does

Books, reschedules, and cancels events on the user's actual Google
Calendar via the `gws` CLI (Google Workspace CLI) already authenticated
in this project — not a suggestion or a draft, a real write to their
calendar. It's the mirror image of the `일정관리` subagent, which only
reads and briefs; if the user just wants to see what's on their
schedule, that's the one to use, not this skill.

## Before you start: check gws authentication

```bash
npx --yes @googleworkspace/cli auth status
```

Check `"scopes"` for `https://www.googleapis.com/auth/calendar`. If it's
missing, the calls below fail with an auth error (exit code 2) instead of
a helpful message, so it's worth checking first. To add the scope
without dropping ones already granted for other services in this
project:

```bash
npx --yes @googleworkspace/cli auth login --services calendar,docs,drive,gmail,forms
```

This opens a browser consent URL — drive it yourself if a
browser-automation tool is available in the session, otherwise share the
URL and ask the user to complete it.

## Anchor "today" before doing any date math

Requests like "다음주 금요일", "내일 오후 3시", "이번 주말" only make sense
relative to the actual current date — don't assume or infer it from
context. Get it for real:

```bash
date "+%Y-%m-%d %A"
```

Default to the `Asia/Seoul` timezone (`+09:00`) unless the user's context
clearly indicates otherwise.

## Creating an event

1. **Extract the concrete fields** from what the user asked for: title
   (`summary`), start time, end time (or duration), location,
   description, attendee emails, recurrence. If they gave a duration but
   no end time, compute it; if neither is given, default to **1 hour**
   for a timed event and say so in your confirmation back to them, rather
   than silently picking something they didn't ask for and never
   mentioning it.

2. **Build the event body.** For a timed event:

   ```json
   {
     "summary": "팀 회의",
     "location": "회의실 A",
     "description": "분기 리뷰",
     "start": {"dateTime": "2026-08-28T15:00:00+09:00", "timeZone": "Asia/Seoul"},
     "end":   {"dateTime": "2026-08-28T16:00:00+09:00", "timeZone": "Asia/Seoul"},
     "attendees": [{"email": "someone@example.com"}],
     "recurrence": ["RRULE:FREQ=WEEKLY;COUNT=4"]
   }
   ```

   For an all-day event, use `{"date": "2026-08-28"}` instead of
   `dateTime`/`timeZone` on both `start` and `end` — and remember the
   Calendar API treats the all-day `end.date` as exclusive (the day
   *after* the last day the event covers), which trips people up on
   multi-day all-day events if you forget it.

3. **Insert it:**

   ```bash
   gws calendar events insert --params '{"calendarId":"primary","sendUpdates":"none"}' --json '<body from step 2>'
   ```

   Default `sendUpdates` to `"none"` so attendees aren't emailed
   automatically. Only switch it to `"all"` if the user explicitly asked
   to notify or invite them — sending mail on someone's behalf on their
   Google account is the kind of side effect worth a heads-up, not a
   silent default.

4. **Confirm in plain language**, in the terms the user used ("금요일
   오후 3시", not the raw RFC3339 string), and include the response's
   `htmlLink` so they can open the event directly to double-check it.

## Updating an event

Never guess which event to touch from a vague reference — look it up
first.

1. **Find it:**

   ```bash
   gws calendar events list --params '{"calendarId":"primary","timeMin":"<range-start>","timeMax":"<range-end>","singleEvents":true,"orderBy":"startTime","q":"<keyword>"}'
   ```

   Always pass `singleEvents: true` with `orderBy: startTime` together —
   this expands recurring events into concrete instances in chronological
   order instead of returning the recurring series as a single item,
   which is what you want when trying to identify *which* occurrence the
   user means. `q` is a free-text filter; a `timeMin`/`timeMax` window
   from what the user said (e.g. "그 회의" said right after discussing
   Friday narrows the search to Friday) usually narrows things down more
   reliably than `q` alone.

2. **Decide from the results:** exactly one match → proceed. Zero
   matches → tell the user you couldn't find it and ask for more detail;
   don't fabricate an event ID. More than one → show the candidates
   (title + time) and ask which one, rather than guessing.

3. **Apply only the changed fields** with `patch` (not `update`, which
   requires resending the entire resource):

   ```bash
   gws calendar events patch --params '{"calendarId":"primary","eventId":"<id>","sendUpdates":"none"}' --json '{"start":{...},"end":{...}}'
   ```

4. **Confirm the change** the same way as for creation.

## Cancelling / deleting an event

Same lookup as updating, but treat this as the highest-care action this
skill performs — there's no in-CLI undo. After finding the single
matching event, show its details (title, date/time, attendees if any)
and get an explicit go-ahead before running:

```bash
gws calendar events delete --params '{"calendarId":"primary","eventId":"<id>","sendUpdates":"none"}'
```

The only time it's fine to skip the extra confirmation is when the user
named the event unambiguously in the same message that asked for the
cancellation (e.g. they quoted the exact title and only one event
matches it) — otherwise, show what you found before deleting it. This
mirrors how you'd already treat any other destructive, hard-to-reverse
action.

## Notes

- Calendar's full-text `q` search can lag a few seconds right after an
  event was just created or patched — if you insert an event and then
  immediately try to look it up again by searching instead of using the
  ID the insert call already gave you, don't be surprised if it comes up
  empty. Prefer the ID you already have over re-searching for something
  you just touched.
- If `gws auth status` shows the `calendar` scope but a call still fails
  with an auth error, the token may predate this skill's requirements —
  re-run the `auth login` command above with the full service list.
- Don't fabricate an event ID, attendee email, or time you weren't given
  or couldn't find by looking — ask instead.
- If the user just wants to know what's on their calendar rather than
  change it, that's the `일정관리` subagent's job, not this skill's.
