# Trivago MCP Tools — Parameter Reference

## `trivago-accommodation-search`

Search by destination name or point of interest.

**Required**
- `query` — destination or point of interest (e.g. "Seoul", "Jeju Island").
- `arrival`, `departure` — `YYYY-MM-DD`, arrival must be in the future and before departure.

**Optional**
- `adults` (min 1), `children` (min 0), `children_ages` (dash-separated, e.g. `10-12-14`)
- `rooms` (must be ≤ adults)
- `country` — ISO alpha-2 (default `US`)
- `currency` — ISO 4217 (default `USD`)
- `language` — locale code (default `EN_US`, includes `KO_KR`)
- `hotel_rating` — boolean flags `1star`..`5star`, multiple selectable
- `review_rating` — boolean flags `rating70`, `rating75`, `rating80`, `rating85` (7.0+/7.5+/8.0+/8.5+)
- `filters` — boolean amenity flags: `airConditioning`, `breakfastIncluded`, `freeCancellation`, `freeWiFi`, `gym`, `kitchen`, `parking`, `petFriendly`, `pool`, `spa`

## `trivago-accommodation-radius-search`

Search by exact coordinates (landmark/neighborhood/address must be resolved to lat/long first — this tool does not accept a place name).

**Required**
- `latitude`, `longitude` — the search center.
- `arrival`, `departure` — same rules as above.

**Optional**
- Identical to `trivago-accommodation-search`: `adults`, `children`, `children_ages`, `rooms`, `country`, `currency`, `language`, `hotel_rating`, `review_rating`, `filters`.

## Response shape (both tools)

Each response includes:
- `system_message` — trivago's own formatting instructions (renders as individual cards, not a table). See SKILL.md Step 4 for how this skill reconciles that with a scannable comparison table.
- `accommodations[]` — each entry has: `accommodation_name`, `price_per_night`, `price_per_stay`, `currency`, `hotel_rating` (0 = unrated), `review_rating`, `review_count`, `top_amenities`, `accommodation_url`, `main_image`, `latitude`/`longitude`, `distance`, `country_city`, `advertisers`.

Notes:
- Prices are pre-formatted strings with currency symbols/commas (e.g. `"39,624 원"`) — strip non-numeric characters before sorting.
- `hotel_rating: 0` means no official star classification, not a bad rating.
