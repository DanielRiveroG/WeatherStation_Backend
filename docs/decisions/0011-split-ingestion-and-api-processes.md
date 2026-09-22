# 0011: Split ingestion and API into separate processes; live data read from RawReadings

**Status:** Accepted. **Supersedes [0007](0007-lock-for-live-data-reads.md)** entirely.

## Context

[0007](0007-lock-for-live-data-reads.md)'s lock-guarded in-memory buffer design assumed the ingestion loop and the
Flask API run in one process. Working out the deployment architecture surfaced a conflict: gunicorn ([0006](0006-flask-for-web-api.md))
normally runs multiple worker processes, but separate workers don't share Python process memory, and the
serial-reading loop can't be duplicated across workers anyway — they'd contend for the same serial port.

## Decision

Split into two independent, long-running processes:

- **The ingestion process** (today's `MainProgram.py` loop): reads the Arduino, buffers 5-minute-window aggregates,
  writes to `RawReadings`, and at midnight computes/writes `DailySummary`
  ([0003](0003-daily-edge-value-scope.md)/[0009](0009-rename-tables-and-daily-summary-aggregates.md)) — unchanged
  in behavior. It no longer needs to share any in-memory state with anything else.
- **The API process** (Flask under gunicorn): purely reads from the SQLite database. `GET /weather/live`
  ([0010](0010-api-endpoints-and-response-shapes.md)) now queries `RawReadings` for its most recent row
  (`ORDER BY Date DESC LIMIT 1`) instead of reading an in-memory buffer.

This removes [0007](0007-lock-for-live-data-reads.md)'s lock entirely — there is no shared in-process state left to
guard.

## Consequences

- SQLite needs to tolerate one process writing while another reads concurrently. Enable **WAL mode**
  (`PRAGMA journal_mode=WAL`) on the database so readers aren't blocked by the ingestion process's writes — SQLite's
  default rollback-journal mode can otherwise raise "database is locked" under overlapping access.
- gunicorn is now free to run multiple workers if ever wanted — no single-worker constraint from this design.
- The two processes become two separate systemd services — see [0012](0012-deployment-systemd-gunicorn-nginx.md).
- `/weather/live`'s freshness is bounded by how recently the ingestion process last wrote a row (every 5 minutes,
  the existing aggregation cadence) — no behavior change from the frontend's point of view, only where the data
  comes from.

## Addendum: schema creation lives only in the ingestion process

"Independent" above means independent memory/process isolation (no shared in-process state) — it doesn't mean
independent deployment lifecycle. In practice the two processes are always run together, with the ingestion
process (`MainProgram.py`) started first. Given that, `initialize_database()` is called only from `MainProgram.py`;
it was originally also called from `Api.py`'s `__main__` block for safety regardless of start order, but that's
removed as unnecessary — the API is never expected to be the first thing run against a fresh database.
