# 0007: Guard live-data buffer access with a lock

**Status:** Superseded by [0011](0011-split-ingestion-and-api-processes.md). Ingestion and the API became separate
processes, so there is no longer any shared in-memory state for a lock to guard — `/weather/live` reads the latest
row from `RawReadings` instead. Left below as the historical record of the reasoning at the time.

## Context

The live-data API endpoint ([0005](0005-web-api-for-live-and-historic-data.md), served by Flask per
[0006](0006-flask-for-web-api.md)) reads the most recent entry of the module-level buffers in
[MainProgram.py](../../MainProgram.py) (e.g. `temperatureList[-1]`). Those same buffers are concurrently appended to
by the serial-reading loop and periodically reset by `time_event` at each 5-minute window boundary. Because Flask
serves requests on their own thread, a read can land at any instant relative to those writes — regardless of how
infrequent the writes are, the overlap is still possible over a long-running service, and can surface as a
momentarily-empty list or an inconsistent value at the reset boundary.

## Decision

Use a lock (`threading.Lock`) shared between the ingestion loop and the Flask app. The ingestion loop acquires it
around appends and around the window-boundary reset in `time_event`; the live-data endpoint acquires it around
reading the last position of the relevant buffer.

## Consequences

- Requires introducing a shared lock object that both [MainProgram.py](../../MainProgram.py) and the Flask app can
  reference — part of the app-structure work still to be sketched.
- Critical sections should stay short (an append, a reset, or reading one element) so the lock doesn't introduce
  noticeable latency in either the ingestion loop or API responses.
- Covers the "live = last element" case decided here; if a future live endpoint needs a broader read (e.g. several
  parameters at once, or a multi-element slice), it should acquire the same lock for consistency.
