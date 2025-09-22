#!/usr/bin/env python3
"""
Import validation script to catch missing imports during build.
This script will attempt to import all modules and catch import errors.
"""

import ast
import sys
import os
from pathlib import Path
from typing import List, Set, Tuple

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def extract_imports(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def validate_imports(file_path: Path) -> List[str]:
    """Validate that all imports in a file can be resolved."""
    errors = []
    
    try:
        # Add the project root to the Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Try to import the module
        module_name = str(file_path.relative_to(project_root)).replace('/', '.').replace('.py', '')
        
        # Skip test files and __init__.py files
        if 'test_' in module_name or module_name.endswith('__init__'):
            return errors
        
        # Skip scripts directory
        if 'scripts' in module_name:
            return errors
        
        try:
            __import__(module_name)
        except ImportError as e:
            errors.append(f"Import error in {file_path}: {e}")
        except Exception as e:
            # This might be expected for some modules that require specific setup
            if "has no attribute" in str(e):
                errors.append(f"Attribute error in {file_path}: {e}")
            elif "logger" in str(e).lower():
                errors.append(f"Logger error in {file_path}: {e}")
    
    except Exception as e:
        errors.append(f"Validation error for {file_path}: {e}")
    
    return errors

def main():
    """Main validation function."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        sys.exit(1)
    
    print("🔍 Validating imports in Python files...")
    
    python_files = find_python_files(str(src_dir))
    all_errors = []
    
    for file_path in python_files:
        errors = validate_imports(file_path)
        all_errors.extend(errors)
    
    if all_errors:
        print("\n❌ Import validation failed:")
        for error in all_errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All imports validated successfully!")

if __name__ == "__main__":
    main()
