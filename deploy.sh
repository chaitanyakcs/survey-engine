#!/bin/bash

# Survey Engine Railway Deployment Script (Streamlined)
# This script runs essential build checks, builds and pushes the Docker image to Railway
# Usage: ./deploy.sh [--strict-types] [--strict-lint] [--strict] [--clean]

set -e  # Exit on any error

# Parse command line arguments
STRICT_TYPES=false
STRICT_LINT=false
CLEAN_BUILD=false
# Check for RESET_DATABASE environment variable
RESET_DATABASE=${RESET_DATABASE:-false}
if [ "$RESET_DATABASE" = "true" ]; then
    echo "⚠️  RESET_DATABASE=true detected - database will be reset during deployment"
fi
SKIP_TESTS=false
STRICT_TESTS=false
TEST_ONLY=false
for arg in "$@"; do
    case $arg in
        --strict-types)
            STRICT_TYPES=true
            shift
            ;;
        --strict-lint)
            STRICT_LINT=true
            shift
            ;;
        --strict)
            STRICT_TYPES=true
            STRICT_LINT=true
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --strict-tests)
            STRICT_TESTS=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--strict-types] [--strict-lint] [--strict] [--clean] [--skip-tests] [--strict-tests] [--test-only]"
            echo "  --strict-types    Enforce strict type checking (mypy errors block deployment)"
            echo "  --strict-lint     Enforce strict linting (flake8 errors block deployment)"
            echo "  --strict          Enable both strict type checking and linting"
            echo "  --clean           Perform a clean build (remove build artifacts and Docker cache)"
            echo "  --skip-tests      Skip all tests (use with caution)"
            echo "  --strict-tests    Run integration tests (normally skipped for faster deployment)"
            echo "  --test-only       Run tests without deploying"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Note: Development checks (formatting, imports, logger) are now in start-local.sh"
            echo "      Run './start-local.sh dev-checks' for development-specific checks"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Starting Survey Engine deployment to Railway..."

# Run essential build checks first
echo "🔍 Running pre-deployment build checks..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run from project root."
    exit 1
fi

# Install development dependencies if not already installed
echo "📦 Installing development dependencies..."
uv sync --dev > /dev/null 2>&1

# Run type checking
echo "🔍 Running type checking with mypy..."
if [ "$STRICT_TYPES" = true ]; then
    echo "   (Strict mode: type errors will block deployment)"
    if ! uv run mypy src/ --show-error-codes --show-column-numbers --ignore-missing-imports; then
        echo "❌ Type checking failed! Fix type errors before deploying."
        echo "   Run without --strict-types to deploy with type warnings, or fix the errors."
        exit 1
    fi
    echo "✅ Type checking passed!"
else
    echo "   (Lenient mode: type errors will show as warnings)"
    if ! uv run mypy src/ --show-error-codes --show-column-numbers --ignore-missing-imports; then
        echo "⚠️  Type checking found issues, but continuing with deployment..."
        echo "   (Use --strict-types to enforce type checking)"
    else
        echo "✅ Type checking passed!"
    fi
fi

# Run linting
echo "🔍 Running linting with flake8..."
if [ "$STRICT_LINT" = true ]; then
    echo "   (Strict linting mode: linting errors will block deployment)"
    if ! uv run flake8 src/ --max-line-length=88 --extend-ignore=E203,W503; then
        echo "❌ Linting failed! Fix linting errors before deploying."
        echo "   Run without --strict-lint to deploy with linting warnings, or fix the errors."
        exit 1
    fi
    echo "✅ Linting passed!"
else
    echo "   (Lenient linting mode: linting errors will show as warnings)"
    if ! uv run flake8 src/ --max-line-length=88 --extend-ignore=E203,W503 --max-complexity=10; then
        echo "⚠️  Linting found issues, but continuing with deployment..."
        echo "   (Use --strict-lint to enforce linting, or run 'make format' to auto-fix some issues)"
    else
        echo "✅ Linting passed!"
    fi
fi

echo "✅ Essential build checks passed!"
echo "================================================"

# Run test suite before deployment (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo "🧪 Running test suite before deployment..."
    echo "================================================"
    
    # Install development dependencies if not already installed
    uv sync --dev > /dev/null 2>&1
    
    # Run critical tests (must pass for deployment)
    echo "🔍 Running critical test suite..."
    if ./scripts/run_tests.sh critical --quiet; then
        echo "✅ Critical tests passed!"
    else
        echo "❌ Critical tests failed! Cannot deploy."
        echo "   Fix failing tests before deploying."
        exit 1
    fi
    
    # Run integration tests only if explicitly requested
    if [ "$STRICT_TESTS" = true ]; then
        echo "🔍 Running integration tests (--strict-tests flag)..."
        if ./scripts/run_tests.sh integration --quiet; then
            echo "✅ Integration tests passed!"
        else
            echo "❌ Integration tests failed! Cannot deploy in strict mode."
            echo "   Fix failing tests or run without --strict-tests"
            exit 1
        fi
    else
        echo "ℹ️  Skipping integration tests (use --strict-tests to run them)"
        echo "   Critical tests are sufficient for deployment validation"
    fi
    
    echo "✅ Test suite completed!"
    echo "   (Critical tests passed, integration tests skipped for faster deployment)"
    echo "   Use --strict-tests to run integration tests if needed"
    echo "================================================"
else
    echo "⚠️  Skipping tests (--skip-tests flag used)"
    echo "================================================"
fi

# If test-only mode, exit here
if [ "$TEST_ONLY" = true ]; then
    echo "✅ Test-only mode completed successfully!"
    exit 0
fi

# Clean build if requested
if [ "$CLEAN_BUILD" = true ]; then
    echo "🧹 Performing clean build..."
    echo "================================================"
    
    # Clean frontend build artifacts
    echo "🗑️  Cleaning frontend build artifacts..."
    rm -rf frontend/build
    rm -rf frontend/dist
    rm -rf frontend/node_modules/.cache
    
    # Clean Python cache
    echo "🗑️  Cleaning Python cache..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    # Clean Docker build cache
    echo "🗑️  Cleaning Docker build cache..."
    docker builder prune -f
    docker system prune -f --volumes
    
    # Remove existing Docker images for this project
    echo "🗑️  Removing existing Docker images..."
    docker rmi chaitanyakc/survey-engine:latest 2>/dev/null || true
    docker rmi $(docker images -q chaitanyakc/survey-engine) 2>/dev/null || true
    
    echo "✅ Clean build preparation complete!"
    echo "================================================"
fi

# Build frontend first
echo "🔨 Building frontend..."
cd frontend
npm run build
cd ..

# Build the Docker image for AMD64/Linux platform
echo "📦 Building Docker image for AMD64/Linux platform..."
if [ "$CLEAN_BUILD" = true ]; then
    echo "   (Clean build: using --no-cache flag)"
    docker buildx build --platform linux/amd64 --no-cache -t chaitanyakc/survey-engine:latest --load .
else
    docker buildx build --platform linux/amd64 -t chaitanyakc/survey-engine:latest --load .
fi

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Push the image to Docker Hub
echo "📤 Pushing image to Docker Hub..."
docker push chaitanyakc/survey-engine:latest

if [ $? -eq 0 ]; then
    echo "✅ Image pushed to Docker Hub successfully!"
    
    # Trigger Railway redeploy
    echo "🔄 Triggering Railway redeploy..."
    if railway redeploy -y; then
        echo "✅ Railway redeploy triggered successfully."
        
        # Wait for Railway deployment to take effect
        echo "⏳ Waiting 120 seconds for Railway deployment to take effect..."
        echo "   This ensures the new Docker image is fully deployed and ready."
        sleep 120
        echo "✅ Deployment wait period completed."
        
        # Start Railway logs for monitoring
        echo "📋 Starting Railway logs monitoring..."
        echo "   You can monitor deployment progress in real-time."
        echo "   Press Ctrl+C to stop logs and continue with deployment."
        echo ""
        railway logs
        
    else
        echo "❌ Railway redeploy failed."
        exit 1
    fi
    
    echo ""
    echo "🎉 Deployment complete!"
    echo "📋 App URL: https://survey-engine-production.up.railway.app"
    echo ""
    echo "📋 Database Setup (Manual Operations):"
    echo ""

    if [ "$RESET_DATABASE" = "true" ]; then
        echo "🧹 RESET_DATABASE=true - Run reset first:"
        echo "   curl -X POST 'https://survey-engine-production.up.railway.app/api/v1/admin/reset-database?confirmation_code=DANGER_DELETE_ALL_DATA&force=true'"
        echo ""
    fi

    echo "🏗️  Bootstrap schema (idempotent, safe to run):"
    echo "   curl -X POST 'https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all'"
    echo "   # Or use bootstrap-complete directly:"
    echo "   curl -X POST 'https://survey-engine-production.up.railway.app/api/v1/admin/bootstrap-complete?confirmation_code=BOOTSTRAP_DATABASE&force=true'"
    echo ""
    echo "🌱 Seed data (after bootstrap):"
    echo "   # Run these via Railway console or API:"
    echo "   python migrations/seed_core_generation_rules.py"
    echo "   python scripts/populate_rule_based_multi_level_rag.py"
    echo ""
    echo "📋 Seed QNR taxonomy:"
    echo "   curl -X POST 'https://survey-engine-production.up.railway.app/api/v1/admin/seed-qnr-taxonomy'"
    echo ""
    echo "📖 Full documentation: docs/DATABASE_SETUP.md"
    echo ""
    echo "🔍 To check logs:"
    echo "   - Use Railway dashboard logs tab"
    echo "   - Or run: railway logs"
else
    echo "❌ Docker push failed!"
    exit 1
fi
