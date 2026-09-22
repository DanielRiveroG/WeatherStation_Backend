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

- [MainProgram.py](MainProgram.py) — entry point and main loop. Reads a line of serial data formatted as
  comma-separated `Key:Value` pairs, parses it via `slice_data`/`store_in_array`, and buffers readings into
  module-level lists (`temperatureList`, `humidityList`, `windSpeedList`, `windDirectionList`, `pressureList`,
  `rainList`) keyed by parameter code (`T`=temperature, `H`=humidity, `W`=wind speed, `D`=wind direction,
  `P`=pressure, `R`=rain). A `sched.scheduler` (`timer`) drives `time_event`, which fires every 60 real seconds and:
  - every 5 minutes: computes the mean of temperature/humidity/pressure/wind speed and the predominant wind
    direction (`most_common`) over the buffered readings, computes accumulated (summed, not averaged) rain, and
    calls `store_weather_parameters_in_database` to write one row to the daily register.
  - at midnight: calls `store_edge_values_in_database` with the day's min/max `EdgeValue`s (edge register), then
    resets them for the next day.
- [Models.py](Models.py) — defines `EdgeValue(value, timestamp)`, a small tracker used for daily min/max readings
  (temperature, humidity, wind). `update_max_edge`/`update_min_edge` update the value and timestamp when a new
  reading exceeds the current extreme; `reset_value` clears both fields (called after the daily edge values are
  flushed to the database).
- [DatabaseOperations.py](DatabaseOperations.py) — SQLite persistence. `store_weather_parameters_in_database` inserts
  a row into `DailyRegister`; `store_edge_values_in_database` inserts a row into `EdgeRegister`. Both build a SQL
  string and hand it to `execute_query`, which opens/closes a fresh `sqlite3.connect('Weather_Data.db')` connection
  per call. Neither the `DailyRegister` nor `EdgeRegister` table schema, nor any DB-creation script, exists yet in
  this repo.

## Target architecture / roadmap

Architecture and design decisions (deployment target, planned features, and how they relate to gaps in the current
code) are tracked as an ordered, numbered decision log in [docs/decisions/](docs/decisions/README.md) — read that
directory for the roadmap rather than looking for it here. Add new decisions there as they're made; don't edit past
entries' content when a decision changes, mark them superseded instead (see that directory's README for the
convention).

## Known issues to be aware of when touching this code

- `execute_query` builds SQL via f-string interpolation rather than parameterized queries. Planned fix:
  `execute_query` takes a `parameters` tuple alongside the query string and passes both to `cursor.execute`; the two
  callers build `?`-placeholder query strings instead of interpolating values directly.
- `most_common` (MainProgram.py) uses Python 2-only APIs (`dict.iteritems`, `numpy.operator`) and does not return its
  result — it currently cannot run under Python 3. Planned fix: `return max(dictionary, key=dictionary.get)`.
- `store_edge_values_in_database` calls `time.today()`, which does not exist on the `time` module.
  [DatabaseOperations.py](DatabaseOperations.py) only imports `timedelta` from `datetime`, not `datetime` itself.
  Planned fix: also import `datetime`, and compute `yesterday = datetime.now() - timedelta(days=1)`.
- Not a bug today, but fragile: `MainProgram.py`'s `time_event` calls `datetime.now()` without importing `datetime`
  directly — it only works because `from Models import *` happens to also pull in `datetime` (`Models.py` imports it
  from the `datetime` module). Worth an explicit `from datetime import datetime` if this code is touched.
