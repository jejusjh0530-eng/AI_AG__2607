# Event JSON reference (for `events.insert` / `events.patch`)

Use this only for cases the `+insert` helper can't express: all-day events, recurrence, custom reminders, or reusing an explicit IANA time zone. For a plain timed event, use `+insert` instead (see SKILL.md Step 3a).

## Timed event

```json
{
  "summary": "팀 회의",
  "location": "3층 회의실",
  "description": "분기 계획 논의",
  "start": {"dateTime": "2026-08-22T15:00:00+09:00", "timeZone": "Asia/Seoul"},
  "end":   {"dateTime": "2026-08-22T16:00:00+09:00", "timeZone": "Asia/Seoul"},
  "attendees": [{"email": "a@example.com"}, {"email": "b@example.com"}]
}
```

## All-day event

Use `date` (not `dateTime`) on both `start` and `end`. `end.date` is **exclusive** — a one-day event ends the day *after* it starts.

```json
{
  "summary": "휴가",
  "start": {"date": "2026-08-25"},
  "end":   {"date": "2026-08-26"}
}
```

## Recurring event

Add an RFC5545 `RRULE` (no `DTSTART`/`DTEND` — those come from `start`/`end`).

```json
{
  "summary": "주간 스탠드업",
  "start": {"dateTime": "2026-08-24T09:00:00+09:00", "timeZone": "Asia/Seoul"},
  "end":   {"dateTime": "2026-08-24T09:15:00+09:00", "timeZone": "Asia/Seoul"},
  "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"]
}
```

Common RRULE snippets: `FREQ=DAILY`, `FREQ=WEEKLY;BYDAY=MO,WE,FR`, `FREQ=MONTHLY;BYMONTHDAY=1`, add `;COUNT=10` or `;UNTIL=20261231T000000Z` to bound it.

## Custom reminders

Omitting `reminders` uses the calendar's default. To override:

```json
{
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "popup", "minutes": 30},
      {"method": "email", "minutes": 1440}
    ]
  }
}
```

## Google Meet link (raw form)

`+insert --meet` covers this normally. Raw equivalent requires the `conferenceDataVersion=1` query param:

```
gws calendar events insert --params '{"calendarId": "primary", "conferenceDataVersion": 1}' --json '{
  "summary": "화상 회의",
  "start": {"dateTime": "...", "timeZone": "Asia/Seoul"},
  "end": {"dateTime": "...", "timeZone": "Asia/Seoul"},
  "conferenceData": {"createRequest": {"requestId": "<any-unique-string>"}}
}'
```

## Sending invites to attendees

Event creation with `attendees` does **not** email them unless `sendUpdates` is set on the request (query param, not body field):

```
gws calendar events insert --params '{"calendarId": "primary", "sendUpdates": "all"}' --json '...'
```

`sendUpdates` accepts `all`, `externalOnly`, or `none` (default). Tell the user which one you used.
