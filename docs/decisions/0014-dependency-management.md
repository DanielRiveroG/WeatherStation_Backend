# 0014: Dependency management — single shared requirements.txt, loosely pinned

**Status:** Accepted

## Context

The project has never had a dependency manifest — `numpy` and `pyserial` (`serial`) are required today, and
`Flask` ([0006](0006-flask-for-web-api.md)) / `gunicorn` ([0012](0012-deployment-systemd-gunicorn-nginx.md)) are
about to be added, with nothing declaring any of them. Two questions needed settling: which tool, and how strict
the version pins should be. A related question — since ingestion and the API are now separate processes
([0011](0011-split-ingestion-and-api-processes.md)) — was whether they should get separate dependency lists.

## Decision

- A plain **`requirements.txt`** — no Poetry/PDM/pyproject.toml-based tooling. Matches the project's existing
  minimal-tooling style (no build system, no packaging); a lock-file-based tool would be more ceremony than value
  for a single-device Pi deployment.
- **Loosely pinned** versions (e.g. `numpy>=1.26`), not exact `pip freeze` pins.
- **One shared file** for the whole project, covering both the ingestion process's dependencies (`numpy`,
  `pyserial`) and the API process's (`Flask`, `gunicorn`) — not split per process. Both are small, and splitting
  would add maintenance overhead without a real resource-pressure reason to justify it on a Pi.

## Consequences

- `requirements.txt` needs to be created at the repo root, listing at least `numpy`, `pyserial`, `Flask`,
  `gunicorn`.
- Because pins are loose, an unattended `pip install -r requirements.txt` on a freshly-provisioned Pi can pull a
  newer minor/patch version than was last tested — acceptable tradeoff for now, but worth remembering if a future
  upgrade ever breaks something unexpectedly on redeploy.
- Both systemd services ([0012](0012-deployment-systemd-gunicorn-nginx.md)) install from the same file into the
  same virtual environment, rather than each having its own.
