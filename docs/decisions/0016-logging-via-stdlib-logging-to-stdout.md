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
