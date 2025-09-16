# PortKeeper

Reserve and manage localhost hosts/ports for starting servers. Transparently updates `.env` and `config.json` files and keeps a local registry so multiple processes and users can coordinate port reservations.

## Features

- **Unique Port Reservations**: Ensures that ports are uniquely reserved within a specified range, preventing conflicts.
- **Concurrency Safety**: Uses file locking to ensure safe port reservation and release operations in concurrent environments.
- **Multi-Port Reservations**: Allows reserving multiple ports at once with a single call using the `count` parameter, ideal for applications needing multiple ports.
- **Flexible Port Ranges**: Supports both default and custom port ranges for reservations.
- **Host-Specific Reservations**: Supports reserving ports for specific hosts, allowing for host-specific configurations.
- **CLI Interface**: Provides a command-line interface for easy port management.

## Install

```bash
python3 -m pip install -U portkeeper
```

For local development (editable install):
```bash
make install-dev
```

## Quick Start (TL;DR)

```bash
# Get a free backend port (service profile 8888–8988) and run a server
python3 -m http.server $(portkeeper port --profile service)

# Or run without $(...) using token replacement
portkeeper run --profile service -- python3 -m http.server {PORT}

# Preflight multiple ports and update .env/config before starting your stack
cat > pk.config.json << 'JSON'
{
  "host": "127.0.0.1",
  "ports": [
    { "key": "SERVICE_PORT",  "preferred": 8888, "range": [8888, 8988] },
    { "key": "FRONTEND_PORT", "preferred": 8080, "range": [8080, 8180] }
  ],
  "outputs": [ { "type": "env", "path": ".env" } ]
}
JSON
portkeeper prepare --config pk.config.json
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
portkeeper reserve --preferred 8888 --range 8888-8988 --hold --owner myapp

# To write to .env file, use:
portkeeper reserve --range 8080-8180
# Then manually update .env with PORT=[reserved_port]

# For different services, specify manually:
portkeeper reserve --range 8888-8988 --hold --owner service
portkeeper reserve --range 8080-8180 --hold --owner frontend

# Generic presets (no product-specific names):
#   service  -> preferred 8888, range 8888-8988, default env key SERVICE_PORT
#   frontend -> preferred 8080, range 8080-8180, default env key FRONTEND_PORT
portkeeper reserve --profile service --write-env
portkeeper reserve --profile frontend --write-env

# Release from registry (best-effort)
portkeeper release 8080

# Show registry json
portkeeper status
```

#### Which `portkeeper` am I running?

Make sure your shell resolves to the expected binary (e.g., project venv):

```bash
which portkeeper
python - << 'PY'
import portkeeper, sys
print('path:', getattr(portkeeper, '__file__', '?'))
print('version:', getattr(portkeeper, '__version__', '?'))
PY

# To force the venv version explicitly
python -m portkeeper.cli status
```

### Command Line Interface

PortKeeper now includes a CLI for easy port management:

```bash
# Reserve a port
portkeeper reserve --host 127.0.0.1 --hold

# Reserve a port within a specific range
portkeeper reserve --range 8000-9000

# Reserve a specific port
portkeeper reserve --port 8080
```

### Reserving a Single Port

```bash
portkeeper reserve
```

This command reserves a single port in the default range (1024-65535).

### Reserving Multiple Ports

```bash
portkeeper reserve --count 3 --range 5000-5100
```

This command reserves 3 ports within the range 5000-5100.

### Reserving a Port with Hold

```bash
portkeeper reserve --hold
```

This reserves a port and holds it open with a socket, preventing other processes from using it even if they don't check the registry.

### Reserving Multiple Ports with Hold

```bash
portkeeper reserve --count 2 --hold --range 5000-5100
```

This reserves 2 ports within the specified range and holds them open with sockets.

### Releasing Ports

Ports are automatically released when the process ends if not held. To manually release:

```bash
portkeeper release 5000
```

Or release multiple ports:

```bash
portkeeper release 5000 5001 5002
```

## Network Scanning for Free Ports and Hosts

PortKeeper can scan your local network to find free ports and hosts:

```bash
# Using the provided bash example
bash examples/bash/port_scan.sh

# Using the provided Python example
python examples/python/network_scan.py
```

### Python API for Network Scanning

```python
from portkeeper import PortRegistry

# Initialize registry
registry = PortRegistry()

# Scan local network for free ports
free_ports_by_host = registry.scan_local_network(port_range=(8000, 8050))

# Reserve a port on any available host
reservation = registry.reserve_network_port(port_range=(8000, 8050), hold=True)
print(f"Reserved port {reservation.port} on host {reservation.host}")
```

## Preflight multiple ports and outputs with `prepare`

Use a single config (JSON or YAML) to reserve several ports and update multiple outputs before starting your stack.

`pk.config.json` example:

```json
{
  "host": "127.0.0.1",
  "ports": [
    { "key": "SERVICE_PORT", "preferred": 8888, "range": [8888, 8988] },
    { "key": "FRONTEND_PORT", "preferred": 8080, "range": [8080, 8180] }
  ],
  "outputs": [
    { "type": "env", "path": ".env" },
    { "type": "json", "path": "config.json", "map": {
      "httpUrl": "https://${SERVICE_HOST:-localhost}:${SERVICE_PORT}",
      "wsUrl":   "wss://${SERVICE_HOST:-localhost}:${SERVICE_PORT}/ws"
    }},
    { "type": "runtime_js", "path": "runtime-config.js", "map": {
      "httpUrl": "https://${SERVICE_HOST:-localhost}:${SERVICE_PORT}",
      "wsUrl":   "wss://${SERVICE_HOST:-localhost}:${SERVICE_PORT}/ws"
    }}
  ]
}
```

YAML example (`pk.config.yaml`):

```yaml
host: 127.0.0.1
ports:
  - key: SERVICE_PORT
    preferred: 8888
    range: [8888, 8988]
  - key: FRONTEND_PORT
    preferred: 8080
    range: [8080, 8180]
outputs:
  - type: env
    path: .env
  - type: json
    path: examples/visual-programming/config.json
    map:
      httpUrl: "https://${SERVICE_HOST:-localhost}:${SERVICE_PORT}"
      wsUrl:   "wss://${SERVICE_HOST:-localhost}:${SERVICE_PORT}/ws"
      visualUrl: "http://${FRONTEND_HOST:-localhost}:${FRONTEND_PORT}"
  - type: runtime_js
    path: examples/visual-programming/runtime-config.js
    map:
      httpUrl: "https://${SERVICE_HOST:-localhost}:${SERVICE_PORT}"
      wsUrl:   "wss://${SERVICE_HOST:-localhost}:${SERVICE_PORT}/ws"
```

Run preflight:

```bash
portkeeper prepare --config pk.config.json
# Optional YAML support (requires pyyaml): portkeeper prepare -c pk.config.yaml
```

- Reserves all ports up front
- Writes `.env` generically (e.g., SERVICE_PORT, FRONTEND_PORT)
- Updates JSON targets (including package.json) and a runtime JS snippet
- Variable expansion supports `${VAR}` placeholders from reserved keys or environment

### Integration: EDPMT (example)

```bash
# In EDPMT repo root
source venv/bin/activate
pip install -e /home/tom/github/dynapsys/portkeeper

# Preflight ports and configs
python -m portkeeper.cli prepare --config pk.config.json

# Start services (wrapper for scripts/start-all.sh)
make start

# Or run frontend via run mode
portkeeper run --profile frontend --env-key FRONTEND_PORT --write-env FRONTEND_PORT --env-path .env -- \
  python3 -m http.server {PORT}
```

### Troubleshooting

#### TypeError: `PortRegistry.reserve() got an unexpected keyword argument 'preferred'`

Cause: CLI and core versions are mismatched (older core signature). Fixes:

```bash
# Ensure you use the intended venv
source /path/to/venv/bin/activate
pip install -U portkeeper

# Force the venv’s CLI invocation
python -m portkeeper.cli status

# If needed, reinstall editable from your repo
pip install -e /path/to/portkeeper
```

As a fallback to print a port using the positional signature:

```bash
python - << 'PY'
from portkeeper.core import PortRegistry
r = PortRegistry().reserve(8888, (8888, 8988), '127.0.0.1', False, None)
print(r.port)
PY
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

## Publishing to PyPI or TestPyPI

PortKeeper provides a streamlined process for building and publishing releases to PyPI or TestPyPI using a combination of `Makefile` rules and a dedicated `publish.sh` script. This section explains how to publish new versions, with detailed steps, diagrams, and examples.

### Publication Workflow

The publication process follows these key steps, ensuring builds are clean, versions are unique, and credentials are handled securely:

```
+-------------------+       +-------------------+       +-------------------+       +-------------------+
| Bump Version      | ----> | Clean Artifacts   | ----> | Build Package     | ----> | Upload to PyPI    |
| (if needed)       |       | (optional)        |       |                   |       | or TestPyPI       |
+-------------------+       +-------------------+       +-------------------+       +-------------------+
```

### Prerequisites

Before publishing, ensure you have:
1. **PyPI/TestPyPI Account**: Register on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/) if you haven't already.
2. **API Token**: Generate an API token for secure authentication. Use `__token__` as the username and the token value as the password (format: `pypi-<YOUR_TOKEN>`).
3. **Credentials Setup**: Configure your credentials using one of these methods to avoid interactive prompts:
   - **Environment Variables**: Set `TWINE_USERNAME` and `TWINE_PASSWORD` in your shell.
   - **Command-Line Arguments**: Use `--username` and `--password` with the `publish.sh` script.
   - **~/.pypirc File**: Add your credentials to the `~/.pypirc` file as shown below.

#### Setting Up ~/.pypirc

Create or edit the file `~/.pypirc` with the following content, replacing `<YOUR_TOKEN>` with your actual token:

```ini
[distutils]
index-servers =
  pypi
  testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-<YOUR_TOKEN>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-<YOUR_TOKEN>
```

### Simplified Usage

The easiest way to publish a new version is to use the `Makefile` rules, which handle version bumping, building, and uploading in a single command. Here are the primary commands:

- **Release a Patch Version to PyPI**: Increments the patch version (e.g., 0.1.11 to 0.1.12), builds, and publishes to PyPI.
  ```bash
  make release-patch
  ```
- **Release to TestPyPI**: Builds and publishes the current version to TestPyPI for testing.
  ```bash
  make publish-test
  ```

For more control, you can use the `publish.sh` script directly with custom options (see detailed examples below).

### Detailed Usage Examples

Here are several scenarios to demonstrate different ways to publish PortKeeper:

1. **Basic Release to PyPI with Version Bump**:
   Use the Makefile to handle everything in one step.
   ```bash
   make release-patch
   ```
   *Output*: Bumps version (e.g., 0.1.11 to 0.1.12), cleans artifacts, builds, and uploads to PyPI.

2. **Publish to TestPyPI for Testing**:
   Test a release on TestPyPI before publishing to PyPI.
   ```bash
   make publish-test
   ```
   *Output*: Builds and uploads the current version to TestPyPI.

3. **Manual Control with publish.sh and Custom Credentials**:
   Use the script directly with explicit credentials for PyPI (avoid interactive prompts).
   ```bash
   scripts/publish.sh --username "__token__" --password "pypi-<YOUR_TOKEN>" --bump patch --clean
   ```
   *Output*: Bumps patch version, cleans artifacts, builds, and uploads to PyPI with provided credentials.

4. **Using Environment Variables for Credentials**:
   Set credentials as environment variables to avoid command-line arguments.
   ```bash
   export TWINE_USERNAME="__token__"
   export TWINE_PASSWORD="pypi-<YOUR_TOKEN>"
   scripts/publish.sh --test --bump minor
   ```
   *Output*: Bumps minor version, builds, and uploads to TestPyPI using environment variables for credentials.

5. **Manual Steps for Full Control**:
   Perform each step manually for maximum control over the process.
   ```bash
   make bump-patch  # Bump patch version
   make clean       # Clean old artifacts
   make build       # Build package
   make publish     # Upload to PyPI
   ```
   *Output*: Increments version, cleans, builds, and publishes to PyPI in separate steps.

### Troubleshooting Common Issues

- **Version Conflict**: If you see "File already exists" on PyPI, ensure you bump the version before publishing:
  ```bash
  make bump-patch
  make publish
  ```
- **Credential Prompt Issues**: If the terminal doesn't support secure input, use environment variables or command-line arguments as shown in examples. For a persistent solution, configure `~/.pypirc`:
  1. Open or create the file `~/.pypirc` with a text editor.
  2. Add the following content, replacing `<YOUR_TOKEN>` with your actual token for PyPI or TestPyPI:
     ```ini
     [distutils]
     index-servers =
       pypi
       testpypi

     [pypi]
     repository = https://upload.pypi.org/legacy/
     username = __token__
     password = pypi-<YOUR_TOKEN>

     [testpypi]
     repository = https://test.pypi.org/legacy/
     username = __token__
     password = pypi-<YOUR_TOKEN>
     ```
  3. Save the file and ensure its permissions are set to readable only by you:
     ```bash
     chmod 600 ~/.pypirc
     ```
  4. Retry the publication command:
     ```bash
     make publish-test  # For TestPyPI
     make publish       # For PyPI
     ```
- **Build Failures**: Ensure your `pyproject.toml` is compliant with PEP 639 (license classifiers removed). If issues persist, clean the virtual environment and rebuild:
  ```bash
  rm -rf .venv
  make build
  ```

### ASCII Workflow Diagrams

#### Full Release Process to PyPI
```
+-------------------+       +-------------------+       +-------------------+       +-------------------+
| Bump Version      | ----> | Clean Artifacts   | ----> | Build Package     | ----> | Upload to PyPI    |
| (make bump-patch) |       | (make clean)      |       | (make build)      |       | (make publish)    |
+-------------------+       +-------------------+       +-------------------+       +-------------------+
```

#### Testing on TestPyPI
```
+-------------------+       +-------------------+       +-------------------+
| Current Version   | ----> | Build Package     | ----> | Upload to TestPyPI|
| (no bump needed)  |       | (make build)      |       | (make publish-test)|
+-------------------+       +-------------------+       +-------------------+
```

#### Automated Patch Release
```
+-------------------+       +-------------------+
| Single Command    | ----> | Complete Release  |
| (make release-patch)      | (Bump, Clean, Build, Publish) |
+-------------------+       +-------------------+
```

## Contributing to PortKeeper

We welcome contributions to PortKeeper! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated. Here's how to get started:

### Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/dynapsys/portkeeper.git
   cd portkeeper
   ```
2. **Set Up Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install Development Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .  # Install PortKeeper in editable mode
   ```
4. **Install Pre-Commit Hooks**:
   ```bash
   pre-commit install
   ```
   This ensures code style consistency with `ruff` linting and formatting on every commit.

### Running Tests

Run the test suite to ensure your changes don't break existing functionality:
```bash
make test
```

### Linting and Formatting

Ensure your code adheres to style guidelines:
```bash
make lint    # Check for style issues with ruff
make format  # Auto-format code with ruff
```

### Submitting Changes

1. **Create a Branch**: Make changes on a feature or bugfix branch.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Commit Changes**: Follow conventional commit messages (e.g., `feat: add multi-port reservation`).
   ```bash
   git commit -m "feat: your descriptive message"
   ```
3. **Push and Create Pull Request**: Push your branch and open a PR on GitHub.
   ```bash
   git push origin feature/your-feature-name
   ```

Please refer to `CONTRIBUTING.md` (coming soon) for detailed guidelines, and check `todo.md` for the project roadmap and pending tasks.

## Project Roadmap

For a detailed list of planned features, improvements, and tasks, see [todo.md](todo.md). Key upcoming priorities include comprehensive unit tests, concurrency correctness, multi-port reservations, and Docker tooling integrations.

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
