# PortKeeper Makefile

.PHONY: help venv install install-dev build publish publish-test test lint format clean version bump-patch

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

venv:
	@$(PY) -m venv $(VENV)
	@$(VENV)/bin/python -m pip install -U pip build twine pytest ruff
	@echo "✅ Virtualenv ready: $(VENV)"

install:
	@$(PIP) install -e .

install-dev: install
	@$(PIP) install -U build twine pytest ruff

build:
	@$(PY) -m build

publish:
	@$(PY) -m twine upload dist/*

publish-test:
	@$(PY) -m twine upload --repository testpypi dist/*

test:
	@$(PY) -m pytest -q

lint:
	@ruff check src

format:
	@ruff format src

clean:
	@rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	@find . -name "__pycache__" -type d -exec rm -rf {} +

version:
	@$(PY) -c "import portkeeper; print(portkeeper.__version__)"

bump-patch:
	@bash scripts/bump-version.sh patch
