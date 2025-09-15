#!/usr/bin/env python3
"""
Reserve a port with PortKeeper and then run a basic HTTP server on that port.

- Prefer 8000; search 8000-8100 if busy
- Update .env (PORT) and config.json (server.host/port)
- Start a simple HTTP server listening on the reserved port

Press Ctrl+C to stop.
"""
from __future__ import annotations

import http.server
import json
import socketserver
from pathlib import Path
from portkeeper import PortRegistry


class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - keep SimpleHTTPRequestHandler API
        if self.path == "/":
            payload = {
                "message": "Hello from PortKeeper example",
                "path": self.path,
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


def main() -> None:
    reg = PortRegistry()

    # Reserve a port; don't hold while server runs, but ensure we update configs first.
    res = reg.reserve(preferred=8000, port_range=(8000, 8100), host="127.0.0.1", hold=False, owner="examples/http")

    # Write env and config for downstream tools
    reg.write_env({"PORT": str(res.port)}, path=".env", merge=True)
    reg.update_config_json({"server": {"host": res.host, "port": res.port}}, path="config.json", backup=True)

    print(f"\n🌐 Starting HTTP server on http://{res.host}:{res.port}\n")

    with socketserver.TCPServer((res.host, res.port), SimpleHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            httpd.server_close()


if __name__ == "__main__":
    main()
