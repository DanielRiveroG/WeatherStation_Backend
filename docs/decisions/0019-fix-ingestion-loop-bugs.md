# 0019: Fix ingestion-loop bugs found while implementing 0018

**Status:** Accepted (implemented)

## Context

Implementing [0018](0018-arduino-autodetect-and-simulation-mode.md) required the ingestion loop to actually run, which
surfaced three real, previously-unnoticed bugs in [MainProgram.py](../../MainProgram.py):

1. `main()` called `timer.enter(...)` then `timer.run()`, which never returns (`time_event` reschedules itself every
   call) — so the `while True` loop that reads sensor data right after it was dead code, never reached. Confirmed:
   with the buffers permanently empty, `numpy.sum(temperatureList) / len(temperatureList)` evaluated to `nan`
   (`0.0 / 0`) rather than crashing, so the process would have silently written `nan` rows forever.
2. Sensor values were never converted from the raw strings `str.split(':')` produces. Confirmed
   `numpy.sum(['20', '24', '22'])` raises `TypeError: the resolved dtypes are not compatible with add.reduce` — so
   fixing bug 1 alone would crash on the first real 5-minute tick.
3. The six 5-minute buffers (`temperatureList`, `humidityList`, etc.) were never cleared after being aggregated —
   every "5-minute mean" was actually a cumulative mean since process start, and the buffers grew unboundedly for
   the life of the process.

## Decision

- Run the scheduler (`timer.run()`) on a background `daemon` thread; the main thread runs the read loop (real
  serial or [0018](0018-arduino-autodetect-and-simulation-mode.md)'s simulated readings).
- Convert `T`/`H`/`P`/`W`/`R` values to `float()` in `store_reading` (wind direction `D` stays a string).
- After each 5-minute aggregation, drain the six buffers (snapshot the contents and clear them) instead of just
  reading them — added a `_drain()` helper.
- Since the scheduler now runs on a separate thread from the read loop, both touch the same buffers and `EdgeValue`
  trackers concurrently. Added `readings_lock` (`threading.Lock`), held by `store_reading` while appending/updating,
  and by `time_event` while draining the 5-minute buffers and while reading/resetting the midnight `EdgeValue`s.
  This is a new, narrower need than [0007](0007-lock-for-live-data-reads.md) (which was about the ingestion process
  and the API process sharing memory, resolved by splitting them into separate processes in
  [0011](0011-split-ingestion-and-api-processes.md)) — this lock only guards the ingestion process's own two
  internal threads against each other, and doesn't reintroduce anything 0011 removed.
- Guarded the 5-minute aggregation with `if temperature_snapshot:` so an aggregation window with no readings yet
  (e.g. right at process startup) skips the `nan`-producing division instead of writing garbage to the database.

## Consequences

- Verified: 8 threads hammering `store_reading` concurrently while draining on a timer lost/duplicated zero
  readings (463,036 appended, 463,036 drained); a 15-second real run of `MainProgram.py` in simulation mode stayed
  alive the whole time and created the database schema correctly.
- The ingestion process can now actually ingest data — this was a hard blocker before, independent of
  [0018](0018-arduino-autodetect-and-simulation-mode.md)/hardware.
