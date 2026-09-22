# 0017: Add a Day column to DailySummary

**Status:** Accepted

## Context

Implementing the `RawReadings`/`DailySummary` schema
([0004](0004-auto-create-database-schema.md)/[0008](0008-database-schema.md)/[0009](0009-rename-tables-and-daily-summary-aggregates.md))
surfaced that `DailySummary` had no column identifying which calendar day a row belongs to. Without one, the
`last7Days`/`lastYear` history queries ([0010](0010-api-endpoints-and-response-shapes.md)) have no direct way to
select a specific day's (or month's) row(s) — the old `EdgeRegister` code had a `Day` column for exactly this
reason, and it was dropped somewhere between decisions.

## Decision

Add **`Day`** (integer, Unix epoch seconds at local midnight for that day) to `DailySummary`, as a plain column —
not unique, not the primary key — consistent with [0008](0008-database-schema.md)'s reasoning that `Id` alone
should be the key, so an insert never fails on a natural-key collision.

## Consequences

- `DailySummary`'s `CREATE TABLE` and insert statement include `Day`.
- `last7Days`/`lastYear` queries filter/group by `Day`.
- No uniqueness constraint means a bug could in principle produce two rows for the same day; that's not prevented
  at the schema level, consistent with [0008](0008-database-schema.md)'s reasoning — it would need to be caught
  elsewhere (e.g. monitoring) if it ever happened.
