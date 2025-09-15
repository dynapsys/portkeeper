#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/bump-version.sh [patch|minor|major]
# Default: patch

BUMP_TYPE=${1:-patch}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
INIT_FILE="$PROJECT_ROOT/src/portkeeper/__init__.py"

if [[ ! -f "$PYPROJECT" ]]; then
  echo "❌ pyproject.toml not found at $PYPROJECT" >&2
  exit 1
fi

# Extract current version
CURRENT=$(grep -E '^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"' "$PYPROJECT" | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/')
if [[ -z "$CURRENT" ]]; then
  echo "❌ Could not find current version in pyproject.toml" >&2
  exit 1
fi

IFS='.' read -r MAJ MIN PAT <<< "$CURRENT"
case "$BUMP_TYPE" in
  patch) PAT=$((PAT + 1));;
  minor) MIN=$((MIN + 1)); PAT=0;;
  major) MAJ=$((MAJ + 1)); MIN=0; PAT=0;;
  *) echo "❌ Unknown bump type: $BUMP_TYPE (use patch|minor|major)" >&2; exit 1;;

esac
NEW_VERSION="${MAJ}.${MIN}.${PAT}"

# Update pyproject.toml
sed -i -E "s/^version\s*=\s*\"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"$NEW_VERSION\"/" "$PYPROJECT"

# Update __init__.py
if [[ -f "$INIT_FILE" ]]; then
  sed -i -E "s/__version__\s*=\s*\"[0-9]+\.[0-9]+\.[0-9]+\"/__version__ = \"$NEW_VERSION\"/" "$INIT_FILE"
fi

echo "✅ Bumped version: $CURRENT -> $NEW_VERSION"
