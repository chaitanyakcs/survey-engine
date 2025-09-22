#!/usr/bin/env python3
"""
Gradual type fixing script.
This script helps fix type errors incrementally by focusing on one file at a time.
"""

import subprocess
import sys
from pathlib import Path

def run_mypy_on_file(file_path: str) -> list[str]:
    """Run mypy on a single file and return errors."""
    try:
        result = subprocess.run(
            ["uv", "run", "mypy", file_path, "--show-error-codes", "--ignore-missing-imports"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return result.stdout.split('\n')
        return []
    except Exception as e:
        print(f"Error running mypy on {file_path}: {e}")
        return []

def get_files_with_errors() -> list[str]:
    """Get list of files that have type errors."""
    try:
        result = subprocess.run(
            ["uv", "run", "mypy", "src/", "--show-error-codes", "--ignore-missing-imports"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return []
        
        files = set()
        for line in result.stdout.split('\n'):
            if line.startswith('src/') and '.py:' in line:
                file_path = line.split(':')[0]
                files.add(file_path)
        return sorted(list(files))
    except Exception as e:
        print(f"Error getting files with errors: {e}")
        return []

def main():
    """Main function to help with gradual type fixing."""
    print("🔍 Gradual Type Fixing Helper")
    print("=" * 40)
    
    files_with_errors = get_files_with_errors()
    
    if not files_with_errors:
        print("✅ No type errors found!")
        return
    
    print(f"Found {len(files_with_errors)} files with type errors:")
    for i, file_path in enumerate(files_with_errors, 1):
        print(f"  {i}. {file_path}")
    
    print("\n🎯 Recommended approach:")
    print("1. Pick one file to fix (start with smaller files)")
    print("2. Run: uv run mypy <file_path> --show-error-codes")
    print("3. Fix the errors in that file")
    print("4. Repeat for the next file")
    
    print("\n📋 Quick commands:")
    for file_path in files_with_errors[:5]:  # Show first 5 files
        print(f"  uv run mypy {file_path} --show-error-codes")
    
    if len(files_with_errors) > 5:
        print(f"  ... and {len(files_with_errors) - 5} more files")

if __name__ == "__main__":
    main()
