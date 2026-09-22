# 0015: Configuration via environment variables and a shared systemd EnvironmentFile

**Status:** Accepted (implemented)

## Context

Settings like the SQLite database path and the gunicorn bind address need to be configurable rather than hardcoded,
especially for a specific Pi deployment. Since deployment is already systemd-based
([0012](0012-deployment-systemd-gunicorn-nginx.md)), the natural mechanism is environment variables rather than a
config file the app has to parse itself.

## Decision

App configuration is read from environment variables (`os.environ`), not a parsed config file. Both systemd
services reference one shared `EnvironmentFile=` so common values — notably the database path, needed by both the
ingestion process and the API process ([0011](0011-split-ingestion-and-api-processes.md)) — aren't duplicated
between the two unit files.

## Consequences

- No new parsing dependency needed (`os.getenv` is sufficient) — consistent with
  [0014](0014-dependency-management.md)'s minimal-tooling stance.
- The exact variable names and full settings list (database path, gunicorn bind host/port, any serial-port
  override, log level — see the still-open logging point) are deferred to implementation time, not decided here.
- The `EnvironmentFile` is a Pi-deployment artifact, alongside the systemd unit files noted in
  [0012](0012-deployment-systemd-gunicorn-nginx.md) — worth version-controlling as a template/example (not the real
  deployed file, since actual paths may be device-specific) in whatever `deploy/` location those end up in.
- The app should fall back to sensible defaults when a variable isn't set, so it still runs locally for development
  without requiring systemd or a hand-written env file.

## Addendum: variable names as implemented

All prefixed `WEATHERSTATION_` to avoid collisions, each with a default so nothing is required to run locally:

| Variable | Default | Used by |
|---|---|---|
| `WEATHERSTATION_DB_PATH` | `Weather_Data.db` | Both (`DatabaseOperations.DATABASE_PATH`) |
| `WEATHERSTATION_API_HOST` | `0.0.0.0` | `Api.py` |
| `WEATHERSTATION_API_PORT` | `5000` | `Api.py` |
| `WEATHERSTATION_LOG_LEVEL` | `INFO` | Both — see [0016](0016-logging-via-stdlib-logging-to-stdout.md) |
| `WEATHERSTATION_SERIAL_PORT` | none (auto-detect) | `MainProgram.py` — overrides [0018](0018-arduino-autodetect-and-simulation-mode.md)'s auto-detection |
| `WEATHERSTATION_SIMULATE` | unset (off) | `MainProgram.py` — already existed, predating this decision, per [0018](0018-arduino-autodetect-and-simulation-mode.md) |

The shared systemd `EnvironmentFile` itself still doesn't exist yet — that's part of [0012](0012-deployment-systemd-gunicorn-nginx.md)'s still-outstanding work.
