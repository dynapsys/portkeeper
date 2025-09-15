# PortKeeper Makefile

.PHONY: help install install-dev build publish publish-test test lint format clean clean-dist version bump-patch bump-minor bump-major release-patch release-minor release-major venv

PY ?= python3
PIP ?= $(PY) -m pip
TWINE ?= $(PY) -m twine
BUILD ?= $(PY) -m build
VENV ?= .venv

help:
	@echo "PortKeeper Makefile targets:"
	@echo "  make install         - pip install -e ."
	@echo "  make install-dev     - install package + dev tools (build, twine, pytest, ruff)"
	@echo "  make build           - Build wheel and sdist (dist/*)"
	@echo "  make publish         - Upload to PyPI (requires TWINE credentials; bumps required if version exists)"
	@echo "  make publish-test    - Upload to TestPyPI"
	@echo "  make release-patch   - Bump patch + build + publish"
	@echo "  make test            - Run tests (pytest)"
	@echo "  make lint            - Ruff check"
	@echo "  make format          - Ruff format"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make clean-dist      - Clean distribution artifacts"
	@echo "  make version         - Print package version"
	@echo "  make bump-(patch|minor|major) - Bump version"

install:
	@$(PIP) install -e .

install-dev: install
	@$(PIP) install -U build twine pytest ruff

venv:
	@if [ ! -d $(VENV) ]; then \
		echo "Creating virtual environment..."; \
		$(PY) -m venv $(VENV); \
	fi
	@$(VENV)/bin/python -m pip install -U pip
	@$(VENV)/bin/python -m pip install build twine pytest ruff
	@echo "✅ Virtualenv ready: $(VENV)"

clean:
	@rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	@find . -name "__pycache__" -type d -exec rm -rf {} +

clean-dist:
	@rm -rf dist *.egg-info src/*.egg-info

build: venv install-dev
	@echo "Building package with virtual environment..."
	@$(VENV)/bin/python -m build || { echo "❌ Build failed. Check error messages above."; exit 1; }

publish: build
	@echo "⚠️ Ensure you have set TWINE_USERNAME and TWINE_PASSWORD environment variables or configured ~/.pypirc"
	@bash scripts/publish.sh || { echo "❌ Publication failed. Check credentials or if version already exists on PyPI."; exit 1; }
	@echo "✅ Successfully published to PyPI"

publish-test: build
	@echo "⚠️ Ensure you have set TWINE_USERNAME and TWINE_PASSWORD environment variables or configured ~/.pypirc"
	@bash scripts/publish.sh --test || { echo "❌ Test publication failed. Check credentials or if version already exists on TestPyPI."; exit 1; }
	@echo "✅ Successfully published to TestPyPI"

release-patch: venv install-dev
	@bash scripts/bump-version.sh patch
	@$(MAKE) clean
	@bash scripts/publish.sh || { echo "❌ Publication failed. Check credentials or if version already exists on PyPI."; exit 1; }
	@echo "✅ Released patch version"

release-minor: venv install-dev
	@bash scripts/bump-version.sh minor
	@$(MAKE) clean
	@bash scripts/publish.sh || { echo "❌ Publication failed. Check credentials or if version already exists on PyPI."; exit 1; }
	@echo "✅ Released minor version"

release-major: venv install-dev
	@bash scripts/bump-version.sh major
	@$(MAKE) clean
	@bash scripts/publish.sh || { echo "❌ Publication failed. Check credentials or if version already exists on PyPI."; exit 1; }
	@echo "✅ Released major version"

bump-patch:
	@bash scripts/bump-version.sh patch

bump-minor:
	@bash scripts/bump-version.sh minor

bump-major:
	@bash scripts/bump-version.sh major

test:
	@$(PY) -m pytest -q

lint:
	@ruff check src

format:
	@ruff format src

version:
	@$(PY) -c "import portkeeper; print(portkeeper.__version__)"
