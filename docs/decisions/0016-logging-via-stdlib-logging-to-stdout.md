# 0016: Logging via the stdlib `logging` module, to stdout

**Status:** Accepted (implemented)

## Context

The codebase currently just uses `print()` (e.g. [MainProgram.py](../../MainProgram.py)'s `time_event`). Since
deployment is systemd-based ([0012](0012-deployment-systemd-gunicorn-nginx.md)) and both services' stdout/stderr are
already captured into `journald`, a simple, low-effort logging setup is enough — the user explicitly doesn't need
anything sophisticated, just something usable to check when something goes wrong.

## Decision

Replace `print()` calls with Python's stdlib `logging` module, configured to log to **stdout** (not files). No log
rotation, log-shipping, or structured/JSON logging — `journald` already handles storage and rotation, and
`journalctl -u <service>` is enough to check on either service. Log level is read from the environment
([0015](0015-configuration-via-environment-variables.md), e.g. `LOG_LEVEL=INFO`, defaulting to `INFO`) rather than
hardcoded.

## Consequences

- No new dependency — `logging` is stdlib.
- `print()` calls in [MainProgram.py](../../MainProgram.py) (and the future Flask API/ingestion-process code) get
  replaced with `logger.info(...)`/`logger.error(...)` etc. as that code is written or touched.
- Nothing beyond this is needed for either systemd service to have inspectable logs — this decision is
  intentionally minimal, matching the project's overall "no more tooling than the task needs" style.

## Addendum: implemented as `logging.basicConfig` per entry point

`MainProgram.py` and `Api.py` each call `logging.basicConfig(level=..., stream=sys.stdout, format='%(asctime)s
%(levelname)s %(name)s: %(message)s')` inside their own `main()`/`if __name__ == '__main__':` — not at module import
time, so importing either module (e.g. from a test) doesn't force a logging configuration. The level comes from
`WEATHERSTATION_LOG_LEVEL` (see [0015](0015-configuration-via-environment-variables.md)'s addendum), defaulting to
`INFO`. `DatabaseOperations.py` just does `logger = logging.getLogger(__name__)` and logs its SQLite errors through
it — it doesn't call `basicConfig` itself, since that's each entry point's responsibility, not a shared module's.
`MainProgram.py`'s per-minute tick logs at `DEBUG` (too frequent for `INFO`); the five-minute and midnight events log
at `INFO`.

## Addendum: log every API request and every successful database write

The user asked for two more things logged, at `INFO`:

- **Every API interaction** — `Api.py` has an `@app.after_request` hook logging `<method> <path>[?query] -> <status>`
  for every request the Flask app handles, including 404s for unmatched routes (registered on `app`, not the
  `weather` blueprint, so it isn't limited to `/weather/...` routes).
- **Every database write** — `store_weather_parameters_in_database` and `store_edge_values_in_database`
  ([DatabaseOperations.py](../../DatabaseOperations.py)) each log a line after their `execute_query` call
  succeeds, naming what was written (the `RawReadings` row's values / the `DailySummary` row's day).

There is still no log *file* — see the parent decision above: stdout only, with no rotation/clearing logic in this
app, since that's `journald`'s job once [0012](0012-deployment-systemd-gunicorn-nginx.md) exists. Until then, running
either process manually prints to whatever terminal is open and nothing is persisted; redirect stdout to a file by
hand (e.g. `python MainProgram.py > mainprogram.log 2>&1`) if you want to keep it during local testing.
