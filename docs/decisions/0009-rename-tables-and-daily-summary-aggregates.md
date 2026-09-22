# 0009: Rename tables; DailySummary gains mean/dominant-direction/accumulated-rain columns

**Status:** Accepted

## Context

Reviewing the frontend's decision log ([WeatherStation_Frontend/docs/decisions/](../../../WeatherStation_Frontend/docs/decisions/README.md) 0010, 0011, 0013, 0016) to define the historic-data API surfaced a gap: the `last7Days`/`lastYear` history views need, per day/month, not just extremes but also **mean temperature/humidity/pressure/wind, dominant wind direction, and accumulated rain** — none of which [0008](0008-database-schema.md)'s `EdgeRegister` holds; it only tracks extremes.

Separately, both existing table names were already misleading: `DailyRegister` ([0008](0008-database-schema.md)) holds 5-minute readings, not daily rows, while `EdgeRegister` was about to gain columns that are not edge/extreme values at all. The frontend's own decision log already uses clearer vocabulary for the same two-tier model — "raw readings" and "daily summary" — so renaming to match keeps terminology consistent across both projects.

## Decision

- Rename `DailyRegister` → **`RawReadings`**. Columns unchanged from [0008](0008-database-schema.md): `Id`, `Wind_Speed`, `Wind_Direction`, `Temperature`, `Humidity`, `Pressure`, `Rain`, `Date`.
- Rename `EdgeRegister` → **`DailySummary`**, keeping all columns from [0008](0008-database-schema.md) (the `Id` PK, `Max_Wind_Gust`/`_Direction`/`_Time`, `Max_Temp`/`Min_Temp`(+`_Time`), `Max_Humidity`/`Min_Humidity`(+`_Time`), `Max_Pressure`/`Min_Pressure`(+`_Time`)), and add:

| Column | Type |
|---|---|
| Mean_Temp | number |
| Mean_Humidity | number |
| Mean_Pressure | number |
| Mean_Wind_Speed | number |
| Dominant_Wind_Direction | string |
| Accumulated_Rain | number |

The new columns are computed once, at the same midnight rollover that already writes the extremes: mean columns are the average of that day's `RawReadings` rows, `Accumulated_Rain` is their sum, and `Dominant_Wind_Direction` is the mode of that day's wind directions (the same `most_common` logic already used for the 5-minute aggregation). The existing extremes still require continuous tracking throughout the day via `Models.EdgeValue` — they cannot be recovered from `RawReadings` afterward (see [0003](0003-daily-edge-value-scope.md)/[0008](0008-database-schema.md)).

## Consequences

- [DatabaseOperations.py](../../DatabaseOperations.py) and the eventual `CREATE TABLE` statements ([0004](0004-auto-create-database-schema.md)) need to use the new table/column names.
- [MainProgram.py](../../MainProgram.py)'s midnight branch of `time_event` needs to compute the new aggregate columns from that day's `RawReadings` rows (one query) in addition to resetting the `EdgeValue` trackers, which it doesn't do today.
- `DailySummary` now holds everything the `last7Days`/`lastYear` historic views need — extremes and means and dominant direction and accumulated rain — in one row per day, resolving the gap found when cross-checking the frontend's data model.
- This completes and renames [0008](0008-database-schema.md)'s schema rather than replacing its per-column decisions (surrogate `Id` PK, Unix epoch timestamps) — those still stand.
