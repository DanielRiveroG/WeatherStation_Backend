# 0001: Deploy as a continuously running service on a Raspberry Pi

**Status:** Proposed

## Context

The program needs to run unattended for long periods, continuously reading from the Arduino weather station and
recording data over time.

## Decision

The deployment target is a Raspberry Pi, running the program continuously (e.g. as a service), rather than as a
manually-started, one-off script.

## Consequences

- The program needs to tolerate transient failures (e.g. a temporarily unreadable serial port, a database write
  error) without crashing outright, since there's no one watching it interactively.
- Startup should be self-sufficient: it shouldn't depend on manual setup steps (e.g. see
  [0002](0002-auto-detect-arduino-serial-port.md) and [0004](0004-auto-create-database-schema.md)).
