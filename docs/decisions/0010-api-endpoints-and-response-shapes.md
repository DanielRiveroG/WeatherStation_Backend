# 0010: API endpoint list and response shapes

**Status:** Accepted. **Revised by [0011](0011-split-ingestion-and-api-processes.md)** (`/weather/live` now reads
the latest `RawReadings` row rather than an in-memory buffer — no change to the response shape from that) **and by
[0013](0013-live-rainfall-is-daily-accumulated.md)** (`/weather/live`'s `rainfallMm` field is renamed
`rainfallTodayMm` and now means the day's accumulated rainfall, not the last 5-minute reading). Everything else
below still stands.

## Context

[0005](0005-web-api-for-live-and-historic-data.md)/[0006](0006-flask-for-web-api.md) call for a Flask web API
serving live and historic data; the frontend's decision log ([WeatherStation_Frontend/docs/decisions/](../../../WeatherStation_Frontend/docs/decisions/README.md)
0009–0016) already assumes a concrete (if unconfirmed) shape for it, built against mocked data. This decision
confirms that shape as the real contract, so both projects can build against the same thing.

The API is **read-only** — ingestion happens internally via the serial-read loop, not through the API.

## Decision

All routes are mounted under the base path **`/weather`**.

### `GET /weather/live`

Returns the most recent reading (per [0007](0007-lock-for-live-data-reads.md), lock-guarded):

```json
{
  "temperatureC": 21.4,
  "humidityPct": 63,
  "pressureHpa": 1013.2,
  "rainfallTodayMm": 2.4,
  "windSpeedKmh": 12.5,
  "windDirection": "NE",
  "recordedAt": "2026-09-22T14:05:00Z"
}
```

(`rainfallTodayMm` per [0013](0013-live-rainfall-is-daily-accumulated.md) — the day's accumulated rainfall, not the
last 5-minute reading.)

`windDirection` is the compass abbreviation (backend-formatted, matching [WeatherStation_Frontend decision 0009](../../../WeatherStation_Frontend/docs/decisions/0009-wind-direction-from-backend-and-last-updated.md) — no raw degrees). `recordedAt` is an ISO 8601 string; internally readings are keyed by Unix epoch seconds ([0008](0008-database-schema.md)/[0009](0009-rename-tables-and-daily-summary-aggregates.md)), converted to ISO 8601 only at the API boundary.

### `GET /weather/history/{parameter}?timespan=today|last7Days|lastYear`

`parameter` is one of `temperature`, `humidity`, `pressure`, `windSpeed`, `rainfall`. Response is an array whose
shape depends on `parameter`, and whose granularity/source depends on `timespan`:

| timespan | granularity | source | max/min or gust present? |
|---|---|---|---|
| `today` | hourly (24 points) | `RawReadings`, grouped by hour | No — only means (no extremes/gust at hourly granularity) |
| `last7Days` | daily (7 points) | `DailySummary`, one row per day | Yes |
| `lastYear` | monthly (12 points) | `DailySummary`, rolled up per calendar month | Yes |

Per-parameter point shape (`timestamp` is always an ISO 8601 string: start of the hour/day/month the point covers):

- `temperature` / `humidity` / `pressure`: `{ timestamp, mean, max?, min? }` — `max`/`min` only for `last7Days`/`lastYear`.
- `windSpeed`: `{ timestamp, meanSpeedKmh, dominantDirection, maxGustKmh?, maxGustDirection? }` — gust fields only for `last7Days`/`lastYear`.
- `rainfall`: `{ timestamp, accumulatedRainMm }`.

These match the frontend's `HistoricValuePoint`/`HistoricWindPoint`/`HistoricRainfallPoint` models exactly.

### `GET /weather/history/{parameter}?start=YYYY-MM-DD&end=YYYY-MM-DD`

Custom range (inclusive, date-only, no time component). The backend decides granularity from the range length —
1 day → `hourly`, ≤30 days → `daily`, >30 days (capped at 366) → `monthly` — using the same per-parameter point
shapes as above, wrapped:

```json
{ "granularity": "hourly", "points": [ ... ] }
```

Monthly roll-up (for both `lastYear` and a >30-day custom range) is computed from that month's `DailySummary` rows:
mean columns average the daily means; `max`/`min` are the max/min of the daily max/min; accumulated rain sums the
daily totals; dominant direction is the mode of the days' dominant directions; max gust (with its direction) is the
max of the days' max gusts, carrying whichever day's gust direction produced it.

### Calendar boundaries

"Today"'s hours, and day/month boundaries generally, use the Raspberry Pi's local system timezone — consistent
with the existing midnight rollover in `MainProgram.py`'s `time_event`, which already uses local time, not UTC.

### Empty periods

If a requested period has no data yet (e.g. a range before the station started recording, or a not-yet-elapsed
bucket), the history endpoints return **`200` with an empty array** (or `{ "granularity": ..., "points": [] }` for
the custom-range endpoint) rather than a `404`. The endpoint itself is valid; there's simply nothing to report yet.

## Consequences

- `RawReadings`/`DailySummary` column names ([0009](0009-rename-tables-and-daily-summary-aggregates.md)) map
  directly to these response fields; the Flask route handlers are effectively a query + a field-name/unit
  translation layer, no new aggregation logic beyond what's described above.
- `WeatherStation_Frontend`'s `environment.apiBaseUrl` needs to be set to wherever this API actually runs, including
  the `/weather` prefix (e.g. `http://<pi-host>:5000/weather`), once deployed — the frontend's existing relative
  paths (`/live`, `/history/...`) then need no code change.
- This is the first decision to reference the frontend project directly; keep this pattern (checking
  `WeatherStation_Frontend/docs/decisions/` before assuming an API shape) for any future endpoint changes, rather
  than the two projects' assumptions drifting apart independently.
