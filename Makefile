# PortKeeper Makefile

.PHONY: help venv install install-dev build publish publish-test test lint format clean version bump-patch release-patch release-minor release-major sign-artifacts

PY ?= python3
PIP ?= $(PY) -m pip
VENV ?= .venv

help:
	@echo "PortKeeper Makefile targets:"
	@echo "  make venv            - Create venv and install dev tools"
	@echo "  make install         - pip install -e ."
	@echo "  make install-dev     - install package + dev tools (build, twine, pytest, ruff)"
	@echo "  make build           - Build wheel and sdist"
	@echo "  make publish         - Upload to PyPI (requires TWINE credentials)"
	@echo "  make publish-test    - Upload to TestPyPI"
	@echo "  make test            - Run tests (pytest)"
	@echo "  make lint            - Ruff check"
	@echo "  make format          - Ruff format"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make version         - Print package version"
	@echo "  make bump-patch      - Bump patch version in pyproject/__init__"
	@echo "  make release-patch   - Bump patch version, build, publish"
	@echo "  make release-minor   - Bump minor version, build, publish"
	@echo "  make release-major   - Bump major version, build, publish"
	@echo "  make sign-artifacts  - Sign distribution artifacts with GPG (if available)"

venv:
	@if [ ! -d $(VENV) ]; then \
		echo "Creating virtual environment..."; \
		$(PY) -m venv $(VENV); \
	fi
	@$(VENV)/bin/python -m pip install -U pip build twine pytest ruff setuptools wheel
	@echo "✅ Virtualenv ready: $(VENV)"

install: venv
	@$(VENV)/bin/pip install -e .

install-dev: install
	@$(VENV)/bin/pip install -U build twine pytest ruff

build: venv install-dev
	@echo "Building package with virtual environment..."
	@$(VENV)/bin/python -m build || { echo "❌ Build failed. Check error messages above."; exit 1; }

publish-test:
	@echo "📦 Publishing to TestPyPI..."
	@bash scripts/publish.sh --test

publish:
	@echo "📦 Publishing to PyPI..."
	@bash scripts/publish.sh

test: venv install
	@echo "Running unit tests with pytest..."
	@$(VENV)/bin/python -m pytest -v tests/

lint: venv install-dev
	@$(VENV)/bin/ruff check src

format: venv install-dev
	@$(VENV)/bin/ruff format src

clean:
	@rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "✅ Cleaned build artifacts"

version: venv install
	@$(VENV)/bin/python -c "import portkeeper; print(portkeeper.__version__)"

bump-patch:
	@bash scripts/bump-version.sh patch

# Version increment rules
release-patch:
	@echo "📦 Releasing new patch version..."
	@bash scripts/publish.sh --bump patch

release-minor:
	@echo "📦 Releasing new minor version..."
	@bash scripts/publish.sh --bump minor

release-major:
	@echo "📦 Releasing new major version..."
	@bash scripts/publish.sh --bump major

# Sign distribution artifacts with GPG (if available)
sign-artifacts:
	@if command -v gpg > /dev/null; then \
		echo "Signing artifacts in dist/ with GPG..."; \
		for f in dist/*; do \
			if [ -f "$$f" ] && [ ! -f "$$f.asc" ]; then \
				echo "Signing $$f"; \
				gpg --armor --detach-sign "$$f"; \
			fi; \
		done; \
		echo "✅ Artifacts signed"; \
	else \
		echo "⚠️ GPG not found, skipping artifact signing"; \
	fi
