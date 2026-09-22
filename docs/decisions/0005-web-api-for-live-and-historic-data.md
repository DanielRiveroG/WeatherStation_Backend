# 0005: Expose a web API for live and historic weather data

**Status:** Proposed

## Context

The collected data (buffered live readings, plus `DailyRegister`/`EdgeRegister` history) currently has no way to be
consumed outside this process — there's no web framework or API layer in the repo.

## Decision

Provide a web API for a separate web application to consume, covering both:

- Live values — the most recent/in-progress readings (e.g. the current buffer or latest computed 5-minute means).
- Historic data — queries over `DailyRegister` and `EdgeRegister`.

## Consequences

- Requires choosing a web framework/library (none chosen yet) and adding it as a dependency.
- The API needs read access to the SQLite database, and to the in-memory live state currently held in
  [MainProgram.py](../../MainProgram.py)'s module-level lists — the live path may need those to be shared with (or
  exposed by) the API process rather than staying private to the ingestion loop, depending on whether the API runs
  in the same process or a separate one.
- Depends on [0004](0004-auto-create-database-schema.md) so the API isn't querying tables that may not exist yet.
