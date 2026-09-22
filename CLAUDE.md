# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

WeatherStation_Backend continuously reads sensor readings from an Arduino weather station over a serial connection,
buffers them, and every five minutes computes and persists summaries to a local SQLite database (`Weather_Data.db`).
Once a day at midnight it also persists that day's edge (min/max) values.

The Arduino sends one line per reading in the format `T:<temperature>,H:<humidity>,R:<rain>,W:<wind_speed>,
D:<wind_direction>,P:<pressure>`.

There is no build system, package manifest, or test suite in this repository. It is run directly with Python 3.

## Running

```
python MainProgram.py
```

Requires the `numpy` and `pyserial` (`serial`) third-party packages; there is no requirements file, so install them
manually if missing.

The Arduino serial connection is currently commented out in [MainProgram.py](MainProgram.py) (`arduinoConnection`),
with a hardcoded sample string (`data = "W:1,R:5,H2"`) used in its place for local testing without hardware attached.

## Architecture

Three modules, no packages:

- [MainProgram.py](MainProgram.py) — entry point and main loop. Calls `initialize_database()` once at startup, then
  reads a line of serial data formatted as comma-separated `Key:Value` pairs, parses it via
  `slice_data`/`store_in_array`, and buffers readings into module-level lists (`temperatureList`, `humidityList`,
  `windSpeedList`, `windDirectionList`, `pressureList`, `rainList`) keyed by parameter code (`T`=temperature,
  `H`=humidity, `W`=wind speed, `D`=wind direction, `P`=pressure, `R`=rain). A `sched.scheduler` (`timer`) drives
  `time_event`, which fires every 60 real seconds and:
  - every 5 minutes: computes the mean of temperature/humidity/pressure/wind speed and the predominant wind
    direction (`most_common`) over the buffered readings, computes accumulated (summed, not averaged) rain, and
    calls `store_weather_parameters_in_database` to write one row to `RawReadings`.
  - at midnight: calls `store_edge_values_in_database` with the day's min/max `EdgeValue`s, which writes one row to
    `DailySummary` (extremes plus mean/dominant-direction/accumulated-rain columns computed by querying that day's
    `RawReadings` rows), then resets the `EdgeValue`s for the next day.
- [Models.py](Models.py) — defines `EdgeValue(value, timestamp)`, a small tracker used for daily min/max readings
  (temperature, humidity, wind). `update_max_edge`/`update_min_edge` update the value and Unix-epoch timestamp when
  a new reading exceeds the current extreme; `reset_value` clears both fields (called after the daily edge values
  are flushed to the database).
- [DatabaseOperations.py](DatabaseOperations.py) — SQLite persistence against `Weather_Data.db`.
  `initialize_database()` creates the `RawReadings` and `DailySummary` tables (`CREATE TABLE IF NOT EXISTS`) if
  they don't exist yet — see [docs/decisions/0008](docs/decisions/0008-database-schema.md),
  [0009](docs/decisions/0009-rename-tables-and-daily-summary-aggregates.md), and
  [0017](docs/decisions/0017-daily-summary-day-column.md) for the schema. `store_weather_parameters_in_database`
  inserts a row into `RawReadings`; `store_edge_values_in_database` inserts a row into `DailySummary`, deriving its
  mean/dominant-direction/accumulated-rain columns from `RawReadings` via `_fetch_daily_means`/
  `_fetch_dominant_direction`. All queries are parameterized (`?` placeholders), not string-interpolated. Pressure
  min/max and the wind gust's own direction aren't tracked anywhere yet, so those `DailySummary` columns are always
  `NULL` for now — tracking them is a still-open gap, not a bug in this code.

## Target architecture / roadmap

Architecture and design decisions (deployment target, planned features, and how they relate to gaps in the current
code) are tracked as an ordered, numbered decision log in [docs/decisions/](docs/decisions/README.md) — read that
directory for the roadmap rather than looking for it here. Add new decisions there as they're made; don't edit past
entries' content when a decision changes, mark them superseded instead (see that directory's README for the
convention).

