#!/usr/bin/env bash
set -euo pipefail

# CLI examples for PortKeeper
# Requirements: portkeeper CLI in PATH (pip install portkeeper)

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

echo "📦 Reserving a port via CLI (prefer 9000, search 9000-9100)..."
portkeeper reserve \
  --preferred 9000 \
  --range 9000 9100 \
  --host 127.0.0.1 \
  --owner examples/cli \
  --write-env PORT \
  --env-path .env

# Load the .env written by the CLI
set -a
. ./.env
set +a

: "${PORT:?PORT not found in .env}"
echo "✅ Reserved PORT=$PORT"

# Start a simple Python HTTP server on the reserved port
# (In a real app, replace this with your server command.)
echo "🌐 Starting python -m http.server on port $PORT (Ctrl+C to stop)"
python3 -m http.server "$PORT"
