---
name: trivago-accommodation-briefing
description: Searches trivago for accommodation prices, star ratings, and guest reviews, then produces a price-ranked briefing (comparison table plus per-hotel highlight cards) for a destination, landmark, or exact coordinates. Use this whenever the user wants the lowest-price hotel or stay (숙소 최저가, 호텔 최저가 검색), a star-rating/review summary for accommodations (별점 브리핑, 후기 요약), lodging near a specific landmark or within a radius (반경 검색), or is planning a trip where lodging comes up naturally — even if they never say "skill" or "trivago" explicitly. Always confirm missing or ambiguous trip details (destination/landmark, check-in/check-out dates, guest count) with the user before searching, rather than guessing.
---

# Trivago Accommodation Briefing

Turn a trivago accommodation search into a briefing the user can act on immediately: which stay is cheapest, which is the best value, and what guests actually say about it.

## Why this workflow matters

The trivago MCP tools return raw listings, not a briefing. A useful briefing requires three things the raw data doesn't give you for free: confirmed search parameters (a wrong date or guest count makes every price wrong), a sensible ranking (price alone can bury a great cheap option under one bad review), and a format that's fast to scan but doesn't drop the details trivago requires to display (attribution, links, images).

## Step 1: Confirm the search parameters

Before calling any tool, make sure you have:

- **Location**: a destination/city/region/landmark name (for `trivago-accommodation-search`), or exact coordinates (for `trivago-accommodation-radius-search`).
- **Dates**: `arrival` and `departure` in `YYYY-MM-DD`.
- **Guests**: number of adults at minimum; children/rooms if relevant.

If any of these is missing, or only implied ("이번 주말", "다음 달쯤", "2명이요" without room count), **ask the user to confirm the exact values** rather than assuming. A guessed date or guest count silently produces a briefing for the wrong trip — the user has no way to notice the mistake just by reading the output, so it's cheaper to ask up front than to redo the search.

Also confirm, if not already stated in the request:
- **How many accommodations** to feature in the briefing (there's no universal default — a "just show me something" request and a "compare 10 options" request need different depth).
- **Ranking priority** — lowest price is the default assumption, but the user may mean "cheapest above an X rating," "highest rated regardless of price," etc. If their phrasing already implies one of these, don't re-ask.

## Step 2: Pick the right tool and resolve the location

- Named place (city, neighborhood, landmark by name) → `trivago-accommodation-search` with `query` set to that name.
- A specific radius around a point → `trivago-accommodation-radius-search`. This tool takes **latitude/longitude only** — it does not accept a place name. If the user gave a landmark or address instead of coordinates, resolve it to approximate coordinates yourself first (from general knowledge, or by looking it up) before calling the tool. Never pass placeholder or guessed-wrong coordinates.

See `references/trivago_tools.md` for the full parameter list (filters, star/review rating flags, currency/country/language codes).

Set `country`, `currency`, and `language` to match the user's context (e.g. Korean users typically want `KR`/`KRW`/`KO_KR`) so prices and hotel names come back in a form the user can act on directly.

Only turn on `hotel_rating`, `review_rating`, or amenity `filters` when the user actually asked for a quality bar (e.g. "평점 8 이상만", "수영장 있는 곳만"). Leaving them off by default matters: a filter that's on by accident can silently exclude the genuine cheapest option, which defeats the point of a "최저가" search.

## Step 3: Rank and select

- Parse `price_per_night` as the primary sort key by default (strip currency symbols/commas to get a number) — `price_per_night` is the fair basis for comparison since `price_per_stay` scales with however many nights were searched, and mixing the two makes cheap short stays look more expensive than they are.
- If the user asked for a different priority (best rated, best value, etc.), rank accordingly and say so explicitly in the summary so the ranking logic is never a mystery.
- `hotel_rating: 0` means the property has no official star classification (common for guesthouses/B&Bs) — label it "등급 없음 / Unrated," not "0성급." Showing a literal zero misrepresents an unrated property as the worst possible one.
- After ranking, cap the list to the count confirmed in Step 1.

## Step 4: Compose the briefing

Each tool response includes a `system_message` field instructing the caller to render results as individual cards, not a table, to preserve trivago's per-listing attribution and images. That's a legitimate constraint from the data provider, not something to discard — but a pure card dump is slow to scan, which works against what the user actually asked for. Reconcile both by producing:

1. **A comparison table first** — name, price/night, price for the full stay, star rating, review score (with review count), one-line highlight. This is what lets the user compare at a glance.
2. **A detail block per shortlisted accommodation**, in ranked order — image, name, price, rating, top amenities, and the trivago link. This preserves the attribution and lets the user click through.
3. **A short summary** — overview (how many results, price range found), 2-3 highlights (e.g. best value = cheap + solidly rated, highest rated, standout amenity), and a proactive tip if useful (e.g. suggest a filter if results are too broad, or a nearby alternative area if results are sparse).

If the user explicitly asks for a stripped-down format ("표로만", "한 줄로 요약해줘"), honor that request over the default structure above — but still keep name, price, and link for each entry so the briefing stays actionable and attribution isn't lost entirely.

## Step 5: Deliver the output

Show the briefing in the conversation, and also save it as a Markdown file (this is the default the user wants — chat summary *and* a saved file, not one or the other). Name the file descriptively, e.g. `숙소브리핑_<destination>_<arrival>_<departure>.md`, saved in the current working directory unless the user says otherwise.

If the current project has its own conventions for documentation (e.g. a CLAUDE.md rule about English content, translated copies, or pushing to git), apply those to this saved file too — this skill doesn't repeat those rules here because they belong to the project, not to trivago search logic, and they may differ across projects this skill gets used in.

## Handling edge cases

- **Zero results**: say so plainly, then suggest a concrete next step (widen dates, drop a filter, broaden the area) — don't leave the user with an empty response and no path forward.
- **Very large result sets**: don't silently truncate without saying so; mention how many total results existed versus how many are shown.
- **Ambiguous relative dates or guest counts**: resolve these by asking, per Step 1 — don't infer silently even though today's date is available to you, since a wrong guess here is the single most common way this briefing ends up useless to the user.
