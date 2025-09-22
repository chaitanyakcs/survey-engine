.PHONY: help install dev-install type-check lint format import-check build-check test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

dev-install: ## Install development dependencies
	uv sync --dev

type-check: ## Run type checking with mypy (lenient mode)
	uv run mypy src/ --show-error-codes --show-column-numbers --ignore-missing-imports

type-check-strict: ## Run strict type checking with mypy (errors block)
	uv run mypy src/ --show-error-codes --show-column-numbers --ignore-missing-imports

lint: ## Run linting with flake8
	uv run flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

format: ## Format code with black and isort
	uv run black src/
	uv run isort src/

import-check: ## Check logger usage
	uv run python scripts/check_logger_usage.py

build-check: dev-install type-check lint import-check ## Run all build checks
	@echo "✅ All build checks passed!"

build-check-strict: dev-install type-check-strict lint import-check ## Run all build checks with strict typing
	@echo "✅ All build checks passed!"

deploy: ## Deploy to Railway (lenient mode)
	./deploy.sh

deploy-strict: ## Deploy to Railway with strict type checking and linting
	./deploy.sh --strict

deploy-strict-types: ## Deploy to Railway with strict type checking only
	./deploy.sh --strict-types

deploy-strict-lint: ## Deploy to Railway with strict linting only
	./deploy.sh --strict-lint

test: ## Run tests
	uv run pytest tests/ -v

clean: ## Clean up build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
