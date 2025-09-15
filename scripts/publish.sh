#!/usr/bin/env bash
set -euo pipefail

# Publish PortKeeper to PyPI or TestPyPI
# Usage: scripts/publish.sh [--test] [--clean] [--username USER] [--password PASS] [--bump BUMP_TYPE]
#   --test: Publish to TestPyPI instead of PyPI
#   --clean: Clean build artifacts before building
#   --username USER: Specify username (or token identifier, e.g., __token__)
#   --password PASS: Specify password (or token value)
#   --bump BUMP_TYPE: Increment version before publishing (patch, minor, major)
#   If username/password not provided, falls back to TWINE_USERNAME/TWINE_PASSWORD env vars or ~/.pypirc

REPO="pypi"
CLEAN="false"
USERNAME=""
PASSWORD=""
BUMP_TYPE=""
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
VENV="$PROJECT_ROOT/.venv"
PY="python3"
PACKAGE_NAME="portkeeper"

while [[ $# -gt 0 ]]; do
  case $1 in
    --test)
      REPO="testpypi"
      shift
      ;;
    --clean)
      CLEAN="true"
      shift
      ;;
    --username)
      USERNAME="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --bump)
      BUMP_TYPE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

echo "📦 Publishing to $REPO"

# Create or reuse virtual environment
if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment at $VENV..."
  "$PY" -m venv "$VENV"
else
  echo "Using existing virtual environment at $VENV..."
fi

# Upgrade pip and install necessary tools
"$VENV/bin/python" -m pip install -U pip
"$VENV/bin/python" -m pip install build twine setuptools wheel

echo "✅ Virtual environment setup complete with necessary tools"

# Bump version if requested
if [ -n "$BUMP_TYPE" ]; then
  echo "🔢 Bumping version ($BUMP_TYPE)..."
  bash "$PROJECT_ROOT/scripts/bump-version.sh" "$BUMP_TYPE"
fi

# Clean build artifacts if requested
if [ "$CLEAN" = "true" ]; then
  echo "🧹 Cleaning build artifacts..."
  rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist" "$PROJECT_ROOT"/*.egg-info "$PROJECT_ROOT/src"/*.egg-info
  find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} +
fi

# Build package
echo "🔨 Building package..."
cd "$PROJECT_ROOT"
"$VENV/bin/python" -m build || { echo "❌ Build failed. Check error messages above."; exit 1; }

echo "✅ Build successful"

# Function to check if version already exists on PyPI or TestPyPI
check_version_unique() {
    local repo=$1
    local package=$2
    local version=$3
    local url=""
    if [ "$repo" == "pypi" ]; then
        url="https://pypi.org/pypi/$package/$version/json"
    else
        url="https://test.pypi.org/pypi/$package/$version/json"
    fi
    if curl -s -f "$url" > /dev/null; then
        return 0  # Version exists
    else
        return 1  # Version does not exist
    fi
}

# Function to upload to TestPyPI
test_upload() {
    CURRENT_VERSION=$("$VENV/bin/python" -c "import portkeeper; print(portkeeper.__version__)")
    check_version_unique "testpypi" "$PACKAGE_NAME" "$CURRENT_VERSION"
    if [ $? -eq 0 ]; then
        echo "❌ Version $CURRENT_VERSION already exists on TestPyPI. Please bump the version."
        exit 1
    fi
    echo "🚀 Uploading to testpypi..."
    echo "⚠️ To avoid interactive prompts, set TWINE_USERNAME and TWINE_PASSWORD environment variables or use --username and --password arguments."
    echo "⚠️ For tokens, use username '__token__' and password 'pypi-<YOUR_TOKEN>'. See README.md for details."
    echo "⚠️ If you encounter issues with password input, ensure your terminal supports secure input or use environment variables."
    TWINE_ARGS=""
    if [ -n "$USERNAME" ]; then
      TWINE_ARGS="--username '$USERNAME'"
    fi
    if [ -n "$PASSWORD" ]; then
      TWINE_ARGS="$TWINE_ARGS --password '$PASSWORD'"
    fi
    eval "$VENV/bin/python -m twine upload --repository testpypi $TWINE_ARGS dist/*" || { echo "❌ Test publication failed. Check credentials or if version already exists on TestPyPI."; echo "💡 Use 'export TWINE_USERNAME=\"__token__\"' and 'export TWINE_PASSWORD=\"pypi-<YOUR_TOKEN>\"' before running this script."; exit 1; }
    echo "✅ Successfully published to TestPyPI"
    echo "✅ View at: https://test.pypi.org/project/$PACKAGE_NAME/$CURRENT_VERSION/"
}

# Function to upload to PyPI
upload() {
    CURRENT_VERSION=$("$VENV/bin/python" -c "import portkeeper; print(portkeeper.__version__)")
    check_version_unique "pypi" "$PACKAGE_NAME" "$CURRENT_VERSION"
    if [ $? -eq 0 ]; then
        echo "❌ Version $CURRENT_VERSION already exists on PyPI. Please bump the version."
        exit 1
    fi
    echo "🚀 Uploading to pypi..."
    echo "⚠️ To avoid interactive prompts, set TWINE_USERNAME and TWINE_PASSWORD environment variables or use --username and --password arguments."
    echo "⚠️ For tokens, use username '__token__' and password 'pypi-<YOUR_TOKEN>'. See README.md for details."
    echo "⚠️ If you encounter issues with password input, ensure your terminal supports secure input or use environment variables."
    TWINE_ARGS=""
    if [ -n "$USERNAME" ]; then
      TWINE_ARGS="--username '$USERNAME'"
    fi
    if [ -n "$PASSWORD" ]; then
      TWINE_ARGS="$TWINE_ARGS --password '$PASSWORD'"
    fi
    eval "$VENV/bin/python -m twine upload $TWINE_ARGS dist/*" || { echo "❌ Publication failed. Check credentials or if version already exists on PyPI."; exit 1; }
    echo "✅ Successfully published to PyPI"
    echo "✅ View at: https://pypi.org/project/$PACKAGE_NAME/$CURRENT_VERSION/"
}

if [ "$REPO" = "testpypi" ]; then
  test_upload
else
  upload
fi
