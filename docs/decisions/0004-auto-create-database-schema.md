# 0004: Auto-create the SQLite database and tables on startup if missing

**Status:** Proposed

## Context

[DatabaseOperations.py](../../DatabaseOperations.py) assumes the database and its schema already exist.
`sqlite3.connect('Weather_Data.db')` will silently create an empty database file if it's missing, but nothing
creates the `DailyRegister`/`EdgeRegister` tables, so `execute_query` fails until they're set up by hand. This
conflicts with unattended deployment ([0001](0001-raspberry-pi-continuous-deployment.md)).

## Decision

On startup, the program should create the database file and the `DailyRegister`/`EdgeRegister` tables if they don't
already exist (e.g. `CREATE TABLE IF NOT EXISTS ...`), rather than assuming manual setup.

## Consequences

- Needs a defined schema for `DailyRegister` and `EdgeRegister` (currently undefined anywhere in the repo) — this
  should account for the additional edge columns from [0003](0003-daily-edge-value-scope.md).
- The schema-creation step should run once at startup, before the main loop begins reading/storing data.
