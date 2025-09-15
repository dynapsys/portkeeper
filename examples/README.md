# PortKeeper Examples

This folder contains practical examples showing how to use PortKeeper to reserve ports, update `.env` and `config.json`, and boot servers safely.

## Prerequisites

- Install PortKeeper:
  ```bash
  python3 -m pip install -U portkeeper
  ```

- Optional dev install (from repository root):
  ```bash
  make install-dev
  ```

## Examples

- `basic_reserve.py` – Reserve a port (optionally within a range), write to `.env` and `config.json`.
- `reserve_and_run_http_server.py` – Reserve a port and start a basic HTTP server on it.
- `cli_examples.sh` – CLI-based reserve/release, demonstrate passing the port to a process.

Run examples:

```bash
cd examples
python3 basic_reserve.py
python3 reserve_and_run_http_server.py
bash cli_examples.sh
```

## Why reserve ports?

- __Avoid conflicts__ when multiple tools run on the same machine.
- __Coordinate__ between separate processes/users via a shared on-disk registry.
- __Automate config__ updates atomically (`.env` and `config.json`).

## Notes

- The `hold=True` option keeps a socket bound in the current process to prevent others from stealing the port, but once that process exits the hold is released.
- When reserving for a server you’re about to start, you can `hold=True` during setup, update configuration files, then release right before binding your actual server.
