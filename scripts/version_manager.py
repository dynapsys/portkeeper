#!/usr/bin/env python3
"""
EDPMT Version Manager
====================
Automatically increment version numbers for publishing
"""

import re
import sys
from pathlib import Path

def get_current_version(file_path):
    """Extract current version from file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for version patterns
        patterns = [
            r'__version__\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
            r'version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
                
        return None
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def increment_patch_version(version_str):
    """Increment patch version (x.y.z -> x.y.z+1)"""
    try:
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
            
        major, minor, patch = parts
        new_patch = str(int(patch) + 1)
        return f"{major}.{minor}.{new_patch}"
        
    except Exception as e:
        print(f"Error incrementing version {version_str}: {e}")
        return None

def increment_minor_version(version_str):
    """Increment minor version (x.y.z -> x.y+1.0)"""
    try:
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
            
        major, minor, patch = parts
        new_minor = str(int(minor) + 1)
        return f"{major}.{new_minor}.0"
        
    except Exception as e:
        print(f"Error incrementing minor version {version_str}: {e}")
        return None

def increment_major_version(version_str):
    """Increment major version (x.y.z -> x+1.0.0)"""
    try:
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")
            
        major, minor, patch = parts
        new_major = str(int(major) + 1)
        return f"{new_major}.0.0"
        
    except Exception as e:
        print(f"Error incrementing major version {version_str}: {e}")
        return None

def update_version_in_file(file_path, old_version, new_version):
    """Update version in file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace version patterns
        patterns_replacements = [
            (rf'(__version__\s*=\s*["\']){old_version}(["\'])', rf'\g<1>{new_version}\g<2>'),
            (rf'(version\s*=\s*["\']){old_version}(["\'])', rf'\g<1>{new_version}\g<2>'),
        ]
        
        updated = False
        for pattern, replacement in patterns_replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
        
        if updated:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        else:
            print(f"No version pattern found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main version manager function"""
    if len(sys.argv) < 2:
        print("Usage: python version_manager.py <increment_type> [files...]")
        print("increment_type: patch, minor, major")
        print("If no files specified, updates __init__.py and setup.py")
        sys.exit(1)
    
    increment_type = sys.argv[1].lower()
    if increment_type not in ['patch', 'minor', 'major']:
        print("Error: increment_type must be 'patch', 'minor', or 'major'")
        sys.exit(1)
    
    # Default files to update
    project_root = Path(__file__).parent.parent
    default_files = [
        project_root / "__init__.py",
        project_root / "setup.py"
    ]
    
    # Use specified files or default files
    files_to_update = []
    if len(sys.argv) > 2:
        files_to_update = [Path(f) for f in sys.argv[2:]]
    else:
        files_to_update = [f for f in default_files if f.exists()]
    
    if not files_to_update:
        print("Error: No files to update found")
        sys.exit(1)
    
    # Get current version from first file
    current_version = get_current_version(files_to_update[0])
    if not current_version:
        print(f"Error: Could not find current version in {files_to_update[0]}")
        sys.exit(1)
    
    print(f"📦 Current version: {current_version}")
    
    # Calculate new version
    if increment_type == 'patch':
        new_version = increment_patch_version(current_version)
    elif increment_type == 'minor':
        new_version = increment_minor_version(current_version)
    elif increment_type == 'major':
        new_version = increment_major_version(current_version)
    
    if not new_version:
        print("Error: Could not calculate new version")
        sys.exit(1)
    
    print(f"🚀 New version: {new_version}")
    
    # Update all files
    success_count = 0
    for file_path in files_to_update:
        print(f"📝 Updating {file_path}...")
        if update_version_in_file(file_path, current_version, new_version):
            print(f"✅ Updated {file_path}")
            success_count += 1
        else:
            print(f"❌ Failed to update {file_path}")
    
    print(f"\n📊 Updated {success_count}/{len(files_to_update)} files")
    
    if success_count > 0:
        print(f"🎉 Version incremented: {current_version} -> {new_version}")
        # Output the new version for use in scripts
        print(f"NEW_VERSION={new_version}")
    else:
        print("❌ No files were updated")
        sys.exit(1)

if __name__ == "__main__":
    main()
