# Decision log

Architecture and design decisions for WeatherStation_Backend, recorded as individual files in this directory so they
can be read and tracked in order. Numbered sequentially by the order they were made; do not renumber existing files.

Each decision is a separate `NNNN-title.md` file with:

- **Status** — `Proposed`, `Accepted`, `Superseded by NNNN`, or `Rejected`. A decision whose code has actually been
  written gets `(implemented)` appended to its status in the index below — the decision log tracks what was
  decided, not what's built, so this is just a marker in the index table, not part of the file itself.
- **Context** — the situation/problem that prompted the decision.
- **Decision** — what was decided.
- **Consequences** — resulting tradeoffs, follow-up work, or gaps relative to the current code.

When a later decision changes or replaces an earlier one, mark the old file's status as `Superseded by NNNN` rather
than editing its content away, so the history stays intact.

## Index

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-raspberry-pi-continuous-deployment.md) | Deploy as a continuously running service on a Raspberry Pi | Proposed |
| [0002](0002-auto-detect-arduino-serial-port.md) | Auto-detect the Arduino's serial port instead of hardcoding it | Proposed |
| [0003](0003-daily-edge-value-scope.md) | Track daily min/max temperature, min/max humidity, min/max pressure, and max wind gust | Proposed (implemented) |
| [0004](0004-auto-create-database-schema.md) | Auto-create the SQLite database and tables on startup if missing | Proposed (implemented) |
| [0005](0005-web-api-for-live-and-historic-data.md) | Expose a web API for live and historic weather data | Proposed |
| [0006](0006-flask-for-web-api.md) | Use Flask for the web API | Accepted |
| [0007](0007-lock-for-live-data-reads.md) | Guard live-data buffer access with a lock | Superseded by 0011 |
| [0008](0008-database-schema.md) | DailyRegister and EdgeRegister schema | Superseded in part by 0009 |
| [0009](0009-rename-tables-and-daily-summary-aggregates.md) | Rename tables; DailySummary gains mean/dominant-direction/accumulated-rain columns | Accepted (implemented) |
| [0010](0010-api-endpoints-and-response-shapes.md) | API endpoint list and response shapes | Revised by 0011, 0013 |
| [0011](0011-split-ingestion-and-api-processes.md) | Split ingestion and API into separate processes; live data read from RawReadings | Accepted |
| [0012](0012-deployment-systemd-gunicorn-nginx.md) | Deployment architecture — two systemd services, gunicorn, and nginx | Accepted |
| [0013](0013-live-rainfall-is-daily-accumulated.md) | Live rainfall reflects the day's accumulated total, not the last reading | Accepted |
| [0014](0014-dependency-management.md) | Dependency management — single shared requirements.txt, loosely pinned | Accepted |
| [0015](0015-configuration-via-environment-variables.md) | Configuration via environment variables and a shared systemd EnvironmentFile | Accepted |
| [0016](0016-logging-via-stdlib-logging-to-stdout.md) | Logging via the stdlib logging module, to stdout | Accepted |
| [0017](0017-daily-summary-day-column.md) | Add a Day column to DailySummary | Accepted (implemented) |
