# Trivago MCP – Available Features

This document describes the tools exposed by the Trivago MCP (Model Context Protocol) integration and how to use them.

## Overview

The Trivago MCP provides two accommodation search tools that query trivago's hotel and accommodation database. Both tools return listings of hotels/accommodations matching the given criteria (dates, occupancy, filters, ratings).

## Tools

### 1. `trivago-accommodation-search`

Search for accommodations and hotels by destination name or point of interest (e.g., a city, region, or landmark name).

**Required parameters**
- `query` – Destination or point of interest (text search, e.g. "Seoul", "Jeju Island").
- `arrival` – Arrival date (`YYYY-MM-DD`). Must be a future date and before `departure`.
- `departure` – Departure date (`YYYY-MM-DD`). Must be after `arrival`.

**Optional parameters**
- `adults` – Number of adults (minimum 1).
- `children` – Number of children (minimum 0).
- `children_ages` – Dash-separated list of children's ages (e.g. `10-12-14`).
- `rooms` – Number of rooms (must be ≤ number of adults).
- `country` – ISO alpha-2 country code for market-specific pricing/content (default `US`).
- `currency` – ISO 4217 currency code for displayed prices (default `USD`).
- `language` – Language code for translated content (default `EN_US`; includes `KO_KR` for Korean).
- `hotel_rating` – Filter by star rating: `1star` through `5star` (boolean flags, multiple selectable).
- `review_rating` – Filter by guest review score: `rating70`, `rating75`, `rating80`, `rating85` (7.0+, 7.5+, 8.0+, 8.5+).
- `filters` – Amenity filters (boolean flags, multiple selectable):
  - `airConditioning`
  - `breakfastIncluded`
  - `freeCancellation`
  - `freeWiFi`
  - `gym`
  - `kitchen`
  - `parking`
  - `petFriendly`
  - `pool`
  - `spa`

**Use case:** General destination-based hotel search, e.g. "Find hotels in Busan for Aug 20–22."

---

### 2. `trivago-accommodation-radius-search`

Search for accommodations and hotels near a specific location using geographic coordinates (landmark, neighborhood, or address), instead of a text query.

**Required parameters**
- `latitude` – Latitude of the search target location.
- `longitude` – Longitude of the search target location.
- `arrival` – Arrival date (`YYYY-MM-DD`). Must be a future date and before `departure`.
- `departure` – Departure date (`YYYY-MM-DD`). Must be after `arrival`.

**Optional parameters**
- Identical to `trivago-accommodation-search`: `adults`, `children`, `children_ages`, `rooms`, `country`, `currency`, `language`, `hotel_rating`, `review_rating`, `filters`.

**Use case:** Radius/proximity search around a specific point, e.g. "Find hotels within range of these exact coordinates near a landmark."

---

## Common Parameter Notes

- **Dates**: Both `arrival` and `departure` use `YYYY-MM-DD` format. `arrival` must be in the future and precede `departure`.
- **Currency/Country**: Support a wide range of ISO codes (40+ countries, 40+ currencies) for localized pricing.
- **Language**: Supports 40+ locale codes for translated hotel content, including `KO_KR` (Korean).
- **Filters and ratings**: All filter/rating fields are boolean flags — multiple can be set to `true` simultaneously to narrow results.

## When to Use Which Tool

| Scenario | Tool |
|---|---|
| Searching by city/region/landmark name | `trivago-accommodation-search` |
| Searching by exact coordinates / radius around a point | `trivago-accommodation-radius-search` |
