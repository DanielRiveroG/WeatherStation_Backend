# 0013: Live rainfall reflects the day's accumulated total, not the last reading

**Status:** Accepted

## Context

[0010](0010-api-endpoints-and-response-shapes.md)'s `GET /weather/live` originally returned `rainfallMm` as the
most recent 5-minute reading (matching `RawReadings.Rain` and the frontend's original `LiveReading.rainfallMm`
assumption). The user pointed out that a single 5-minute rain amount isn't very informative on a live dashboard —
the day's accumulated rainfall so far is what's actually useful to see at a glance.

## Decision

`GET /weather/live` returns the day's accumulated rainfall so far, computed as
`SUM(Rain) FROM RawReadings WHERE Date >= <start of today, local time>` — consistent with
[0011](0011-split-ingestion-and-api-processes.md)'s "live data is a DB query, not in-memory state" design, so no new
tracked state is needed. The field is renamed to **`rainfallTodayMm`**, making the "today, not the last interval"
semantics explicit in the name rather than relying on a doc comment alone — the ambiguity of the old name is exactly
what prompted this change.

## Consequences

- Revises [0010](0010-api-endpoints-and-response-shapes.md)'s `/weather/live` response shape: `rainfallMm` →
  `rainfallTodayMm`.
- The frontend's `LiveReading.rainfallMm` (`src/app/models/live-reading.model.ts`) was built against the original,
  now-incorrect 5-minute-interval assumption and needs updating to `rainfallTodayMm` with the corrected semantics —
  the same kind of correction as the wind-direction fix in
  [WeatherStation_Frontend decision 0009](../../../WeatherStation_Frontend/docs/decisions/0009-wind-direction-from-backend-and-last-updated.md).
- `RawReadings.Rain` itself is unchanged — it still stores each 5-minute window's own rain amount
  ([0008](0008-database-schema.md)); only the live endpoint's derived value changes.
- At local midnight the accumulated total naturally resets to 0 as the query's day window rolls over — no explicit
  reset logic needed, unlike the `EdgeValue` trackers.
