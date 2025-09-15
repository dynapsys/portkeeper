# PortKeeper

Reserve and manage localhost hosts/ports for starting servers. Transparently updates `.env` and `config.json` files and keeps a local registry so multiple processes and users can coordinate port reservations.

## Features

- Reserve a free port (preferred port and/or range)
- Optionally hold the port by binding a dummy socket
- Release reservation (and close the held socket)
- Atomic updates to `.env` and `config.json` (+ optional backup)
- Simple file-locking to avoid races (fcntl / msvcrt / fallback)
- Context manager API and a tiny CLI (`portkeeper`)

## Install

```bash
python3 -m pip install -U portkeeper
```

For local development (editable install):
```bash
make install-dev
```

## Usage

### Python API

```python
from portkeeper import PortRegistry

reg = PortRegistry()
# Prefer 8888, then search 8888-8988; bind to 127.0.0.1
res = reg.reserve(preferred=8888, port_range=(8888, 8988), host="127.0.0.1", hold=False, owner="myapp")

# Write/merge .env
reg.write_env({"PORT": str(res.port)}, path=".env", merge=True)

# Update config.json atomically (backup config.json.bak if present)
reg.update_config_json({"server": {"host": res.host, "port": res.port}}, path="config.json", backup=True)
```

Context manager:
```python
from portkeeper import PortRegistry

with PortRegistry().reserve(preferred=8080, port_range=(8080, 8180), hold=True) as r:
    # start your server with r.host, r.port
    pass  # server init here
# automatically released
```

### CLI

```bash
# Reserve preferred 8888 or a port in 8888..8988, hold it, and print JSON
portkeeper reserve --preferred 8888 --range 8888 8988 --hold --owner myapp

# Write .env with key=PORT
portkeeper reserve --preferred 8080 --range 8080 8180 --write-env PORT --env-path .env

# Release from registry (best-effort; sockets held by other processes cannot be forcibly closed)
portkeeper release 8080

# Show registry json
portkeeper status
```

## Examples

- See `examples/` for:
  - Basic reserve + `.env` + `config.json`: `examples/basic_reserve.py`
  - Reserve + run simple HTTP server: `examples/reserve_and_run_http_server.py`
  - CLI workflow: `examples/cli_examples.sh`
  - Docker patterns: `examples/docker/README.md`

## Docker integration

See `examples/docker/README.md` for a few common patterns:
- Compose + `.env` (recommended for dev)
- `docker run` + `.env`
- App image with configurable internal port

## Tests

Run tests:
```bash
make install-dev
make test
```

Tests cover:
- Reserving ports with ranges and preferred ports
- Holding ports and preventing rebinds while held
- Atomic writes to `.env` and `config.json`
- CLI `reserve` and `release`

## Lint & Format

```bash
make lint
make format
```

## Build & Publish

Build artifacts:
```bash
make build
```

Publish (requires PyPI credentials via environment variables or `~/.pypirc`):
```bash
make publish           # to PyPI
make publish-test      # to TestPyPI
```

If you see `HTTP 400 File already exists`, bump the version and retry:
```bash
make bump-patch && make publish
```

One-liner release flows:
```bash
make release-patch
make release-minor
make release-major
```

## Author

**Tom Sapletta**  
🏢 Organization: softreck  
🌐 Website: [softreck.com](https://softreck.com)  

Tom Sapletta is a software engineer and the founder of softreck, specializing in system automation, DevOps tools, and infrastructure management solutions. 
With extensive experience in Python development and distributed systems, Tom focuses on creating tools that simplify complex development workflows.

### Professional Background
- **Expertise**: System Architecture, DevOps, Python Development
- **Focus Areas**: Port Management, Infrastructure Automation, Development Tools
- **Open Source**: Committed to building reliable, well-tested tools for the developer community

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

Copyright 2025 Tom Sapletta

Apache-2.0
