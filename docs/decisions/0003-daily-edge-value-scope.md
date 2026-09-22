# 0003: Track daily min/max temperature, min/max humidity, min/max pressure, and max wind gust

**Status:** Implemented. `Models.py`'s `EdgeValue` pair for pressure and a `GustEdgeValue` (value + timestamp +
direction, populated by pairing each reading's `W` with that same reading's `D`) now exist and feed
`DailySummary`'s `Max_Pressure`/`Min_Pressure`/`Max_Wind_Gust`/`Max_Wind_Gust_Direction` columns — closing the gap
noted below. The "gust as a genuinely different, short-duration measurement" nuance in the second consequence below
was not pursued; the gust is still the max of the same per-reading wind speed samples used for the average, just
now paired with a direction.

## Context

Today [Models.py](../../Models.py)'s `EdgeValue`, as used from [MainProgram.py](../../MainProgram.py), only tracks
max/min temperature, max/min humidity, and a single max wind value — there is no pressure edge tracking at all, and
"max wind" is not distinguished from a wind gust (it's currently just the max of the same per-reading wind speed
samples used for the 5-minute average).

## Decision

The daily edge register should record: min/max temperature, min/max humidity, min/max pressure, and max wind gust.

## Consequences

- Add min/max pressure tracking (an `EdgeValue` pair, analogous to temperature/humidity) alongside the existing
  ones in [MainProgram.py](../../MainProgram.py).
- Wind gust is conceptually a short-duration peak, not just the max of the same samples averaged for wind speed —
  this may require the Arduino/sketch to report gust distinctly from sustained wind speed, or a different sampling
  approach on the backend side, rather than reusing `maxWind` as-is.
- [DatabaseOperations.py](../../DatabaseOperations.py)'s `store_edge_values_in_database` and the `EdgeRegister`
  schema ([0004](0004-auto-create-database-schema.md)) need columns for min/max pressure and max wind gust.
