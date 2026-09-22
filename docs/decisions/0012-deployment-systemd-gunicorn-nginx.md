# 0012: Deployment architecture — two systemd services, gunicorn, and nginx

**Status:** Accepted

## Context

Refines [0001](0001-raspberry-pi-continuous-deployment.md)'s "run continuously... as a service" into concrete
infrastructure, now that ingestion and the API are two separate processes
([0011](0011-split-ingestion-and-api-processes.md)). Also settles how the Angular frontend gets served on the same
device.

## Decision

- **Two systemd services** on the Pi: one running the ingestion loop, one running the Flask API under gunicorn.
  systemd gives auto-restart on crash, start/stop control, ordering (e.g. wait for the serial device), and captures
  stdout/stderr into `journald` as the log sink.
- **gunicorn** serves the Flask app — Flask's built-in dev server isn't meant for production.
- **nginx** serves the built Angular static files and reverse-proxies `/weather`
  ([0010](0010-api-endpoints-and-response-shapes.md)) to gunicorn, so the browser only ever talks to one origin —
  sidesteps CORS entirely, and centralizes TLS/gzip/caching in one place.
- **Apache was considered and rejected** for the frontend/proxy role — heavier than needed for serving static files
  and reverse-proxying; nginx is the more standard lightweight choice for this on a Pi.

## Consequences

- New dependency: `gunicorn`, added to the Python dependency list (still open — see the dependency-management
  discussion). nginx is a system package + config file, not a Python dependency.
- Two systemd unit files (ingestion, API) plus an nginx site config are needed — Pi-deployment artifacts worth
  version-controlling in this repo (e.g. under a `deploy/` directory) rather than existing only by hand on the
  device; exact location to be decided when they're actually written.
- `WeatherStation_Frontend`'s `environment.apiBaseUrl` should be a same-origin relative path (e.g. `/weather`) once
  nginx is proxying, not a separate host:port.
- Because ingestion and the API are already independent processes ([0011](0011-split-ingestion-and-api-processes.md)),
  each systemd service can be restarted/redeployed independently without affecting the other.
