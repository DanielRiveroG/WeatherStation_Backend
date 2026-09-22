# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

WeatherStation_Backend has two independent entry points sharing one SQLite database (`Weather_Data.db`):

- An **ingestion process** ([MainProgram.py](MainProgram.py)) that continuously reads sensor readings from an
  Arduino weather station over a serial connection, buffers them, and every five minutes computes and persists
  summaries to the database. Once a day at midnight it also persists that day's edge (min/max) values.
- A **read-only Flask API** ([Api.py](Api.py)) that serves live and historic weather data by querying that same
  database — see [docs/decisions/0011](docs/decisions/0011-split-ingestion-and-api-processes.md) for why these are
  two separate processes rather than one.

The Arduino sends one line per reading in the format `T:<temperature>,H:<humidity>,R:<rain>,W:<wind_speed>,
D:<wind_direction>,P:<pressure>`.

There is no build system or test suite in this repository. It is run directly with Python 3.

## Running

```
pip install -r requirements.txt
python MainProgram.py   # ingestion process — auto-detects the Arduino's serial port
python Api.py           # API process, http://localhost:5000
```

Only `MainProgram.py` calls `initialize_database()` on startup — the two processes are always run together with
`MainProgram.py` started first, so it alone is responsible for the schema existing (see
[docs/decisions/0011](docs/decisions/0011-split-ingestion-and-api-processes.md)'s addendum).

`MainProgram.py` auto-detects the Arduino's serial port (`find_arduino_port()`, matching known vendor IDs or an
"arduino" description — see [docs/decisions/0018](docs/decisions/0018-arduino-autodetect-and-simulation-mode.md))
and raises if none is found. Set `WEATHERSTATION_SIMULATE=1` to skip hardware entirely and generate synthetic
readings instead, for local/frontend testing without an Arduino attached — same parsing/aggregation/DB-write code
path either way.

Configuration is via environment variables (see
[docs/decisions/0015](docs/decisions/0015-configuration-via-environment-variables.md)'s addendum for the full
list), all optional with sensible defaults: `WEATHERSTATION_DB_PATH`, `WEATHERSTATION_API_HOST`/`_API_PORT`,
`WEATHERSTATION_LOG_LEVEL`, `WEATHERSTATION_SERIAL_PORT` (overrides auto-detection), `WEATHERSTATION_SIMULATE`.
Both entry points log via the stdlib `logging` module to stdout (see
[docs/decisions/0016](docs/decisions/0016-logging-via-stdlib-logging-to-stdout.md)), not `print()`.

## Architecture

Four modules, no packages:

- [MainProgram.py](MainProgram.py) — entry point and main loop. Calls `initialize_database()` once at startup, then
  runs the scheduler (`timer.run()`, see below) on a background daemon thread while the main thread loops reading
  serial data (real, via `connect_to_arduino()`, or simulated, per
  [docs/decisions/0018](docs/decisions/0018-arduino-autodetect-and-simulation-mode.md)) — this split is required
  because `timer.run()` never returns (`time_event` reschedules itself every call), so it can't share a thread with
  the read loop. Each line is comma-separated `Key:Value` pairs; `slice_data` parses a whole line into a
  `{code: value}` dict first (order-independent) and hands it to `store_reading`, which converts values to `float`
  (except `D`, kept as a compass string) and buffers readings — under `readings_lock`, since the read loop and the
  scheduler thread both touch this state — into module-level lists (`temperatureList`, `humidityList`,
  `windSpeedList`, `windDirectionList`, `pressureList`, `rainList`) keyed by parameter code (`T`=temperature,
  `H`=humidity, `W`=wind speed, `D`=wind direction, `P`=pressure, `R`=rain). Parsing a full line at once (rather
  than one code at a time) is what lets the `W` handling look up that same reading's `D` value, needed to pair a
  wind gust with its direction. A `sched.scheduler` (`timer`) drives `time_event`, which fires every 60 real seconds
  and:
  - every 5 minutes: under `readings_lock`, drains (snapshots and clears — `_drain()`) the six buffers, then
    computes the mean of temperature/humidity/pressure/wind speed and the predominant wind direction
    (`most_common`) over that snapshot, computes accumulated (summed, not averaged) rain, and calls
    `store_weather_parameters_in_database` to write one row to `RawReadings`. Skipped if the snapshot is empty
    (e.g. right at startup), rather than dividing by zero.
  - at midnight: under `readings_lock`, calls `store_edge_values_in_database` with the day's min/max `EdgeValue`s
    (temperature, humidity, pressure) and `maxWindGust` (a `GustEdgeValue`, carrying the gust's own wind direction),
    which writes one row to `DailySummary` (extremes plus mean/dominant-direction/accumulated-rain columns computed
    by querying that day's `RawReadings` rows), then resets all of them for the next day.
- [Models.py](Models.py) — defines `EdgeValue(value, timestamp)`, a small tracker used for daily min/max readings
  (temperature, humidity, pressure). `update_max_edge`/`update_min_edge` update the value and Unix-epoch timestamp
  when a new reading exceeds the current extreme; `reset_value` clears both fields. `GustEdgeValue` extends it with
  a `direction` field, set alongside the value/timestamp whenever `update_max_edge(value, direction)` finds a new
  peak — used for the wind gust, which needs to remember which direction the wind was blowing at its peak, not just
  the peak speed.
- [DatabaseOperations.py](DatabaseOperations.py) — SQLite persistence against `Weather_Data.db`.
  `initialize_database()` creates the `RawReadings` and `DailySummary` tables (`CREATE TABLE IF NOT EXISTS`) if
  they don't exist yet — see [docs/decisions/0008](docs/decisions/0008-database-schema.md),
  [0009](docs/decisions/0009-rename-tables-and-daily-summary-aggregates.md), and
  [0017](docs/decisions/0017-daily-summary-day-column.md) for the schema. `store_weather_parameters_in_database`
  inserts a row into `RawReadings`; `store_edge_values_in_database` inserts a row into `DailySummary`, combining the
  extremes/gust it's passed with mean/dominant-direction/accumulated-rain columns derived from `RawReadings` via
  `_fetch_daily_means`/`_fetch_dominant_direction`. Also exposes read functions for the API
  (`fetch_latest_raw_reading`, `fetch_rain_accumulated_since`, `fetch_raw_readings`, `fetch_daily_summaries`). All
  queries are parameterized (`?` placeholders), not string-interpolated.
- [Api.py](Api.py) — the Flask API, per [docs/decisions/0010](docs/decisions/0010-api-endpoints-and-response-shapes.md).
  All routes are under a `/weather` blueprint. `GET /weather/live` reads the latest `RawReadings` row plus today's
  accumulated rain (`rainfallTodayMm`, per [0013](docs/decisions/0013-live-rainfall-is-daily-accumulated.md)) —
  no in-memory state, no dependency on `MainProgram.py`. `GET /weather/history/<parameter>` takes either
  `?timespan=today|last7Days|lastYear` or `?start=YYYY-MM-DD&end=YYYY-MM-DD`; `parameter` is one of `temperature`,
  `humidity`, `pressure`, `windSpeed`, `rainfall`. `today`/a single-day custom range bucket `RawReadings` by local
  hour in Python (`_hourly_points`); `last7Days`/a ≤30-day custom range read `DailySummary` rows directly
  (`_daily_points`); `lastYear`/a >30-day custom range roll `DailySummary` rows up by calendar month
  (`_monthly_points`, `_rollup_month`), per [0009](docs/decisions/0009-rename-tables-and-daily-summary-aggregates.md)'s
  rollup rule (mean of means, max/min of maxes/mins, sum of rain, mode of dominant directions, max of gusts carrying
  that gust's own direction). All `timestamp` fields are ISO 8601 UTC (`Z`-suffixed) — note that during DST this can
  make a bucket's date look one day off from its "true" local calendar date/month when read as a raw string (the
  underlying instant and the grouping are still correct; a consumer converting back to local time, e.g. the
  frontend rendering in the same timezone as the Pi, will show the right date).

## Target architecture / roadmap

Architecture and design decisions (deployment target, planned features, and how they relate to gaps in the current
code) are tracked as an ordered, numbered decision log in [docs/decisions/](docs/decisions/README.md) — read that
directory for the roadmap rather than looking for it here. Add new decisions there as they're made; don't edit past
entries' content when a decision changes, mark them superseded instead (see that directory's README for the
convention).

