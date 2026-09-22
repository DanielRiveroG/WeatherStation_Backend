# 0002: Auto-detect the Arduino's serial port instead of hardcoding it

**Status:** Proposed

## Context

[MainProgram.py](../../MainProgram.py) currently has the serial connection line commented out, with the port
hardcoded (`/dev/ttyACM0`). On a Raspberry Pi ([0001](0001-raspberry-pi-continuous-deployment.md)) the device path
an Arduino enumerates as can vary (e.g. across reboots, reconnects, or different Pi units), so a hardcoded path is
fragile for unattended deployment.

## Decision

The program should scan available serial ports at startup and identify/connect to the one the weather station is
attached to, rather than relying on a fixed, hardcoded device path.

## Consequences

- Requires enumerating serial ports (e.g. via `serial.tools.list_ports`) and a way to distinguish the weather
  station from other serial devices (e.g. matching on USB vendor/product ID, or a handshake/identification string
  sent by the Arduino sketch).
- The program should handle the case where no matching port is found (e.g. retry rather than crash), consistent
  with [0001](0001-raspberry-pi-continuous-deployment.md).
