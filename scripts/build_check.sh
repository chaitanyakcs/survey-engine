#!/bin/bash
set -e

echo "🔍 Running build-time checks..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run from project root."
    exit 1
fi

# Install development dependencies if not already installed
echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

# Run type checking
echo "🔍 Running type checking with mypy..."
mypy src/ --show-error-codes --show-column-numbers

# Run linting
echo "🔍 Running linting with flake8..."
flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

# Run logger usage check
echo "🔍 Running logger usage check..."
python3 scripts/check_logger_usage.py

# Run formatting check
echo "🔍 Checking code formatting..."
black --check src/
isort --check-only src/

echo "✅ All build checks passed!"
