#!/usr/bin/env python3
"""
Check for proper logger usage in Python files.
This script will catch issues like missing logger imports or incorrect logger usage.
"""

import ast
import sys
from pathlib import Path
from typing import List, Set

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []
    for file_path in Path(directory).rglob("*.py"):
        # Skip __pycache__ and .git directories
        if '__pycache__' in str(file_path) or '.git' in str(file_path):
            continue
        python_files.append(file_path)
    return python_files

def check_logger_usage(file_path: Path) -> List[str]:
    """Check for proper logger usage in a Python file."""
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Check for logger usage
        has_logger_usage = False
        has_logger_import = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'logger':
                        has_logger_usage = True
                    elif isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'logger':
                        has_logger_usage = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'logging':
                        has_logger_import = True
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'logging':
                    has_logger_import = True
                elif node.module and 'logging' in node.module:
                    has_logger_import = True
        
        # Check for logger variable assignment
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'logger':
                        has_logger_import = True
                        break
        
        if has_logger_usage and not has_logger_import:
            errors.append(f"Missing logger import in {file_path}")
        
        # Check for self.logger usage (which might be incorrect)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == 'self' and node.attr == 'logger':
                    # Check if the class has a logger attribute defined
                    class_has_logger = False
                    for class_node in ast.walk(tree):
                        if isinstance(class_node, ast.ClassDef):
                            for class_item in class_node.body:
                                if isinstance(class_item, ast.Assign):
                                    for target in class_item.targets:
                                        if isinstance(target, ast.Name) and target.id == 'logger':
                                            class_has_logger = True
                                            break
                                elif isinstance(class_item, ast.FunctionDef) and class_item.name == '__init__':
                                    for init_item in class_item.body:
                                        if isinstance(init_item, ast.Assign):
                                            for target in init_item.targets:
                                                if isinstance(target, ast.Attribute) and target.attr == 'logger':
                                                    class_has_logger = True
                                                    break
                    
                    if not class_has_logger:
                        errors.append(f"Potential self.logger usage without logger attribute in {file_path}")
    
    except Exception as e:
        errors.append(f"Error checking {file_path}: {e}")
    
    return errors

def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        sys.exit(1)
    
    print("🔍 Checking logger usage in Python files...")
    
    python_files = find_python_files(str(src_dir))
    all_errors = []
    
    for file_path in python_files:
        errors = check_logger_usage(file_path)
        all_errors.extend(errors)
    
    if all_errors:
        print("\n❌ Logger usage issues found:")
        for error in all_errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All logger usage is correct!")

if __name__ == "__main__":
    main()
