# 0018: Arduino port auto-detection, with a simulation mode for hardware-less testing

**Status:** Accepted (implemented)

## Context

[0002](0002-auto-detect-arduino-serial-port.md) called for auto-detecting the Arduino's serial port instead of a
hardcoded path. Separately, the user wants to run the backend locally with no Arduino attached at all, to validate
the frontend/backend integration end-to-end before hardware is available.

## Decision

- **Auto-detection** (`find_arduino_port()` in [MainProgram.py](../../MainProgram.py)): scans
  `serial.tools.list_ports.comports()` and matches a port whose vendor ID is the official Arduino VID (`0x2341`) or
  a common clone USB-serial chip's VID (`0x1A86` CH340, `0x0403` FTDI), or whose description contains "arduino".
  This is a best-effort default, not verified against real hardware yet — expect to refine the match once an actual
  board is tested.
- **Simulation mode**: `WEATHERSTATION_SIMULATE=1` (env var) skips port detection entirely and generates synthetic
  readings (`generate_simulated_reading()`) every `SIMULATED_READING_INTERVAL_SECONDS` (5s), fed through the exact
  same `slice_data`/`store_reading` pipeline as real data — so parsing, buffering, aggregation, DB writes, and the
  API are all exercised identically to a real run.
- Without simulation mode, if no port is found, `connect_to_arduino()` raises a `RuntimeError` with a clear message
  rather than retrying — [0002](0002-auto-detect-arduino-serial-port.md) suggested retrying instead of crashing for
  unattended deployment, but that's deferred; for now this relies on systemd's restart-on-crash
  ([0012](0012-deployment-systemd-gunicorn-nginx.md)) once that's set up, rather than custom retry logic in the app.

## Consequences

- No dependency on real hardware to test the API/frontend integration locally.
- The VID/description heuristic is unverified against the actual weather station's board — revisit once hardware
  is in hand.
- `WEATHERSTATION_SIMULATE` is the first environment-variable-based config to actually exist in code, ahead of
  [0015](0015-configuration-via-environment-variables.md)'s broader config work.
