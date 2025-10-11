#!/bin/bash

# Survey Engine Railway Deployment Script (Streamlined)
# This script runs essential build checks, builds and pushes the Docker image to Railway
# Usage: ./deploy.sh [--strict-types] [--strict-lint] [--strict] [--clean]

set -e  # Exit on any error

# Parse command line arguments
STRICT_TYPES=false
STRICT_LINT=false
CLEAN_BUILD=false
AUTO_MIGRATE=false
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
        --auto-migrate)
            AUTO_MIGRATE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--strict-types] [--strict-lint] [--strict] [--clean] [--auto-migrate]"
            echo "  --strict-types    Enforce strict type checking (mypy errors block deployment)"
            echo "  --strict-lint     Enforce strict linting (flake8 errors block deployment)"
            echo "  --strict          Enable both strict type checking and linting"
            echo "  --clean           Perform a clean build (remove build artifacts and Docker cache)"
            echo "  --auto-migrate    Automatically run database migrations after deployment"
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
        
        # Wait for deployment to complete if auto-migrate is enabled
        if [ "$AUTO_MIGRATE" = true ]; then
            echo "⏳ Waiting for deployment to complete and transformers to load..."
            
            # Wait for transformers to load by checking the health endpoint
            HEALTH_URL="https://survey-engine-production.up.railway.app/api/v1/admin/health"
            MAX_WAIT_ATTEMPTS=60  # 60 attempts * 10 seconds = 10 minutes max
            WAIT_COUNT=0
            
            echo "   Checking if server is ready (transformers loading)..."
            while [ $WAIT_COUNT -lt $MAX_WAIT_ATTEMPTS ]; do
                echo "   Attempt $((WAIT_COUNT + 1))/$MAX_WAIT_ATTEMPTS - checking server health..."
                if curl -s "$HEALTH_URL" | grep -q '"status":"healthy"'; then
                    echo "✅ Server is ready! Transformers have loaded."
                    break
                else
                    echo "   Server not ready yet, waiting 10 seconds..."
                    sleep 10
                    WAIT_COUNT=$((WAIT_COUNT + 1))
                fi
            done
            
            if [ $WAIT_COUNT -eq $MAX_WAIT_ATTEMPTS ]; then
                echo "⚠️  Server health check timed out after 10 minutes."
                echo "   Proceeding with migration attempts anyway..."
            fi
            
            # Try to run migrations with retries
            echo "🗄️  Running database migrations..."
            MIGRATION_URL="https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all"
            MAX_RETRIES=5
            RETRY_COUNT=0
            
            while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                echo "   Migration attempt $((RETRY_COUNT + 1))/$MAX_RETRIES..."
                if curl -s -X POST "$MIGRATION_URL" | grep -q '"status":"success"'; then
                    echo "✅ Database migrations completed successfully!"
                    break
                else
                    echo "⚠️  Migration attempt failed, retrying in 10 seconds..."
                    sleep 10
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                fi
            done
            
            if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
                echo "❌ Database migrations failed after $MAX_RETRIES attempts."
                echo "   Please run manually: curl -X POST $MIGRATION_URL"
            fi
        fi
    else
        echo "❌ Railway redeploy failed."
        exit 1
    fi
    
    echo ""
    echo "🎉 Deployment complete!"
    echo "📋 Next steps:"
    echo "   1. Railway is redeploying your service with the latest image"
    echo "   2. Your app will be available at: https://survey-engine-production.up.railway.app"
    echo ""
    if [ "$AUTO_MIGRATE" = true ]; then
        echo "✅ Database migrations were automatically executed"
        echo "   Verify migration status:"
        echo "   curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status"
    else
        echo "🗄️  Database Migration:"
        echo "   After deployment completes, run database migrations:"
        echo "   curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all"
        echo ""
        echo "   Verify migration status:"
        echo "   curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status"
        echo ""
        echo "   💡 Tip: Use --auto-migrate flag to automatically run migrations"
    fi
    echo ""
    echo "🔍 To check logs:"
    echo "   - Use Railway dashboard logs tab"
    echo "   - Or run: railway logs"
else
    echo "❌ Docker push failed!"
    exit 1
fi
