# PortKeeper TODO / Roadmap

Status legend: [ ] pending • [~] in progress • [x] done

## 0.1.x (stabilization)
- [x] Initial package scaffold (`pyproject.toml`, `src/`, CLI `portkeeper`)
- [x] Core API: `PortRegistry.reserve()/release()`, `write_env()`, `update_config_json()`
- [x] Basic file locking (fcntl/msvcrt/fallback)
- [x] Examples: Python API, CLI, Docker/Compose patterns
- [x] Makefile: build/test/lint/format/publish; simplified publish flow
- [x] README: usage, tests, docker examples, publish workflow
- [ ] Improve CLI help and examples in `--help` text
- [ ] Polish error messages and exit codes for CLI

## 0.2.0 (functionality + quality)
- [ ] Tests: add comprehensive unit tests
  - [ ] `tests/conftest.py` to set `PYTHONPATH=src`
  - [ ] Core: preferred/range selection, hold semantics, release correctness
  - [ ] File ops: `.env` merge, atomic writes and backups, `config.json` update
  - [ ] CLI: `reserve` JSON output, `--write-env`, `status`, `gc`
- [ ] Concurrency correctness
  - [ ] Add tests for concurrent `reserve()` calls (threads/processes)
  - [ ] Validate lock contention and fairness
- [ ] Registry health
  - [ ] TTL/heartbeat to auto-GC stale entries
  - [ ] `gc` improvements: configurable policy (pid check, bind check, ttl)
- [ ] Multi-port reservations
  - [ ] API to reserve a set/list of ports atomically (all-or-nothing)
  - [ ] Release bulk reservations
- [ ] UX
  - [ ] Add `--json` pretty output toggle in CLI
  - [ ] Add `--registry` and `--lock` CLI flags (override env/def)
  - [ ] Add `--no-backup` for `update_config_json`
- [ ] Cross-platform
  - [ ] Windows CI run for locking fallback
  - [ ] macOS CI run for file ops reliability

## 0.3.0 (integrations + DX)
- [ ] Docker tooling
  - [ ] Compose generator: helper script to inject reserved ports into env
  - [ ] `portkeeper compose up` convenience wrapper (optional)
- [ ] Pre-commit & linters
  - [ ] Add `.pre-commit-config.yaml` with ruff, end-of-file-fixer, trailing-whitespace
  - [ ] Configure `ruff.toml` with rules and format profile
- [ ] CI/CD (GitHub Actions)
  - [ ] Lint + Test matrix: py39..py313 on ubuntu-latest, windows-latest, macos-latest
  - [ ] Build/publish on tag vX.Y.Z to TestPyPI, manual approve to PyPI
- [ ] Documentation site (optional)
  - [ ] mkdocs or pdoc with API reference and guides

## Stretch goals
- [ ] UDP support (investigate use cases; optional feature flag)
- [ ] Named reservations (labels, metadata, owners, process pid)
- [ ] Reservation lease/renewal model (daemon or library heartbeat)
- [ ] JSON-RPC/HTTP control endpoint (run `portkeeperd` as a service)
- [ ] Language bindings (Node/Python interop via CLI or socket protocol)

## Developer experience
- [ ] Add `requirements-dev.txt` for contributors (pytest, ruff, build, twine)
- [ ] Add `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`
- [ ] Add `CHANGELOG.md` and release notes template

## Performance & reliability
- [ ] Benchmark large-range scan performance and optimize
- [ ] Optional randomization within range to reduce collision bursts
- [ ] Telemetry hooks (count reservations, durations) – behind env flag

## Security
- [ ] Validate input ranges and host strings robustly
- [ ] Harden registry file parsing against corruption
- [ ] Optional signature of `config.json` updates (future)

## Docs (deep dive topics)
- [ ] Atomic file updates and cross-platform guarantees
- [ ] Locking strategies and fallbacks (fcntl/msvcrt/temp-file)
- [ ] Docker/Compose patterns (advanced scenarios, multiple ports)
- [ ] Integrating with frameworks (Flask, FastAPI, aiohttp)

## Examples to add
- [ ] Reserve multiple ports for HTTP + HTTPS + WS simultaneously
- [ ] Integrate with `uvicorn`/`gunicorn` startup scripts
- [ ] Advanced Compose with multiple services reserving distinct ports
- [ ] Local orchestration scripts for monorepos

## Done (recent)
- [x] Publish 0.1.0 to PyPI
- [x] Add `scripts/publish.sh` with error guidance for duplicate versions
- [x] Switch to SPDX license string (Apache-2.0)
- [x] Docker examples: compose/run, prepare scripts
- [x] Makefile: simplified, no forced venv, release targets (bump+build+publish)

---

Notes
- Current local version: see `make version` (pyproject `version` / `__version__`).
- If PyPI rejects an upload with "File already exists", run `make bump-patch && make publish`.



- zadaniem portkeeper jest przed uruchomieniem aplikacji dopasowanie w zmiennych .env, docker, package.json, itd portow aby byly wolne w trakcie uruchamiania aplikacji
- uywaj generycznych nazw dla zmiennych, czy to w docker, czy w .env a nie zapisuj hardkodowanych zmiennych typu visual, edmpt, to sa nazwy wlasne, zmien ten kod, aby komendy byly proste i byly wykonywane w tle, przed uruchomieniem uslugi 
- i testowaly dostepnosc portow i aktualizuowaly wszystkie lub wybrane zmienne w docker, .env, package.json, itd 
- w zaleznosci od typu projektu, przed samym uruchomieniem powinny byc sprawdzone wszystkie porty i zapisane bezposrednio w zmiennych w zalaeznsoci od konfiurgruacji projektu