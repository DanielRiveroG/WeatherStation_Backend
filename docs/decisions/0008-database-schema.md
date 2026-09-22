# 0008: DailyRegister and EdgeRegister schema

**Status:** Accepted. **Superseded in part by [0009](0009-rename-tables-and-daily-summary-aggregates.md)**: the two
tables are renamed (`DailyRegister`→`RawReadings`, `EdgeRegister`→`DailySummary`) and `DailySummary` gains
mean/dominant-direction/accumulated-rain columns beyond the extremes below. The column definitions, `Id` primary
key choice, and Unix-epoch timestamp choice below still stand — only the table names and `DailySummary`'s full
column set change.

## Context

[0004](0004-auto-create-database-schema.md) requires the database schema to be created automatically, but the
columns for `DailyRegister`/`EdgeRegister` were never defined (the current
[DatabaseOperations.py](../../DatabaseOperations.py) code just assumes tables that don't exist anywhere). Separately,
[0003](0003-daily-edge-value-scope.md) called for max wind gust tracking without specifying whether the gust's wind
direction is captured too.

## Decision

Two tables, for now:

**DailyRegister** — one row per 5-minute aggregation window:

| Column | Type |
|---|---|
| Id | integer, primary key, autoincrement |
| Wind_Speed | number |
| Wind_Direction | string |
| Temperature | number |
| Humidity | number |
| Pressure | number |
| Rain | number |
| Date | integer (Unix epoch seconds) |

**EdgeRegister** — one row per day, written at midnight:

| Column | Type |
|---|---|
| Id | integer, primary key, autoincrement |
| Max_Wind_Gust | number |
| Max_Wind_Gust_Direction | string |
| Max_Wind_Gust_Time | integer (Unix epoch seconds) |
| Max_Temp | number |
| Max_Temp_Time | integer (Unix epoch seconds) |
| Min_Temp | number |
| Min_Temp_Time | integer (Unix epoch seconds) |
| Max_Humidity | number |
| Max_Humidity_Time | integer (Unix epoch seconds) |
| Min_Humidity | number |
| Min_Humidity_Time | integer (Unix epoch seconds) |
| Max_Pressure | number |
| Max_Pressure_Time | integer (Unix epoch seconds) |
| Min_Pressure | number |
| Min_Pressure_Time | integer (Unix epoch seconds) |

This refines [0003](0003-daily-edge-value-scope.md): the max wind gust now also records the wind direction at the
time of the gust, not just the speed.

Both tables use a surrogate autoincrement `Id` as primary key rather than the timestamp itself, chosen for
robustness (a clock reset, NTP correction, or double-fired scheduler tick won't collide with an existing row and
silently fail the insert). The project targets a single weather station, so `Date`'s uniqueness across stations was
not a factor in this choice. All timestamp columns store Unix epoch seconds as an `integer`, rather than ISO 8601
text.

## Consequences

- Replaces the current `Day`/`Hour` string split in [DatabaseOperations.py](../../DatabaseOperations.py) with a
  single `Date` epoch-integer column on `DailyRegister`; the existing `store_weather_parameters_in_database` /
  `store_edge_values_in_database` queries need rewriting to match this schema (and to use parameterized queries —
  see the known issue in [CLAUDE.md](../../CLAUDE.md)).
- `Models.EdgeValue` ([Models.py](../../Models.py)) currently tracks max/min temperature, humidity, and a single
  max wind value — it needs a pressure pair and a gust-with-direction variant to produce all the columns above (see
  [0003](0003-daily-edge-value-scope.md)).
