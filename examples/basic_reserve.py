#!/usr/bin/env python3
"""
Basic PortKeeper usage example:
- Reserve a free port (prefer 8888; search 8888-8988 otherwise)
- Write PORT to .env (merge=true)
- Update config.json with host/port (atomic)
"""
from __future__ import annotations

import json
from pathlib import Path
from portkeeper import PortRegistry


def main() -> None:
    reg = PortRegistry()

    # Reserve a port, prefer 8888, search 8888-8988 if busy.
    res = reg.reserve(preferred=8888, port_range=(8888, 8988), host="127.0.0.1", hold=False, owner="examples/basic")

    print(json.dumps({"host": res.host, "port": res.port, "held": res.held}, indent=2))

    # Write .env (merge = True by default)
    reg.write_env({"PORT": str(res.port)}, path=".env", merge=True)

    # Update config.json (atomic write with backup)
    reg.update_config_json({"server": {"host": res.host, "port": res.port}}, path="config.json", backup=True)

    print("\n✅ Wrote .env and config.json in", Path.cwd())


if __name__ == "__main__":
    main()
