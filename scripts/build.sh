#!/usr/bin/env bash
set -euo pipefail

# Build wheel and sdist for PortKeeper
python3 -m pip install -U build
python3 -m build

echo "✅ Build finished. Artifacts in ./dist"
