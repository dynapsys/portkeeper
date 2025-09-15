#!/bin/bash

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo "${YELLOW}📦 Publishing to PyPI with automatic version increment...${NC}"

# Ensure setuptools and twine are installed
echo "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import setuptools" &> /dev/null; then
    echo "${YELLOW}Installing setuptools...${NC}"
    pip3 install setuptools
fi

if ! command -v twine &> /dev/null; then
    echo "${YELLOW}Installing twine...${NC}"
    pip3 install twine
fi

# Function to increment version
increment_version() {
  local bump_type=$1
  echo "${YELLOW}🔢 Auto-incrementing $bump_type version...${NC}"
  
  # Read current version from pyproject.toml
  if ! current_version=$(grep "version =" pyproject.toml | head -1 | cut -d '"' -f 2); then
    echo "${RED}❌ Error: Could not find version in pyproject.toml${NC}"
    exit 1
  fi
  
  if [ -z "$current_version" ]; then
    echo "${RED}❌ Error: Version not found in pyproject.toml${NC}"
    exit 1
  fi
  
  IFS='.' read -r major minor patch <<< "$current_version"
  case $bump_type in
    "major")
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    "minor")
      minor=$((minor + 1))
      patch=0
      ;;
    "patch")
      patch=$((patch + 1))
      ;;
    *)
      echo "${RED}❌ Invalid bump type: $bump_type${NC}"
      exit 1
      ;;
  esac
  new_version="$major.$minor.$patch"
  echo "${YELLOW}📈 Bumping version from $current_version to $new_version${NC}"
  
  # Update version in pyproject.toml
  if ! sed -i "s/version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml; then
    echo "${RED}❌ Failed to update version in pyproject.toml${NC}"
    exit 1
  fi
  
  echo "${GREEN}✅ Version updated to $new_version${NC}"
}

# Auto-increment patch version
increment_version "patch"

# Clean previous builds
echo "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "${YELLOW}🏗️ Building package...${NC}"
if python3 -m build; then
    echo "${GREEN}✅ Package built successfully${NC}"
else
    echo "${RED}❌ Package build failed${NC}"
    exit 1
fi

# Upload to PyPI
echo "${YELLOW}🚀 Uploading to PyPI...${NC}"
if twine upload dist/*; then
    echo "${GREEN}✅ Published to PyPI successfully${NC}"

    # Get the new version for confirmation
    NEW_VERSION=$(grep "version =" pyproject.toml | head -1 | cut -d '"' -f 2)
    echo "${GREEN}🎉 New version ${NEW_VERSION} is now live on PyPI!${NC}"
else
    echo "${RED}❌ Upload to PyPI failed${NC}"
    exit 1
fi
