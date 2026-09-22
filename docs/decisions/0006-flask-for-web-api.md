# 0006: Use Flask for the web API

**Status:** Accepted

## Context

[0005](0005-web-api-for-live-and-historic-data.md) calls for a web API exposing live and historic weather data, but
no framework had been chosen yet. The existing codebase ([MainProgram.py](../../MainProgram.py)) is plain,
synchronous Python: a `sched`-driven loop reading serial data and writing to SQLite, with no async patterns
anywhere. The two realistic candidates considered were Flask and FastAPI.

FastAPI would provide automatic request validation and OpenAPI docs for free, but is async-first — adopting it
would mean either introducing async just for the API layer or bridging sync and async code, for a handful of
read-only endpoints over SQLite where that complexity buys little.

## Decision

Use Flask for the web API. It is synchronous (matches the existing ingestion code's style), minimal, and easy to
run alongside the background thread doing the serial-read/scheduler loop.

## Consequences

- Adds `Flask` as a project dependency (still no requirements file yet — see the gap noted in [CLAUDE.md](../../CLAUDE.md)).
- The ingestion loop ([MainProgram.py](../../MainProgram.py)) and the Flask app need to run in the same process
  without blocking each other — e.g. the ingestion loop on a background thread, Flask serving requests on the main
  thread (or vice versa).
- No automatic request/response validation or generated API docs (unlike FastAPI); add these manually if/when
  needed.
