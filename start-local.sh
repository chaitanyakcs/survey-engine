#!/bin/bash

# Survey Engine Startup Script
# Handles database migrations, seeding, and application startup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_MIGRATIONS_DIR="migrations"
# Rules are seeded via migrations, no separate seeding needed
APP_PORT=${PORT:-8080}
FASTAPI_PORT=${FASTAPI_PORT:-8000}

echo -e "${BLUE}🚀 Starting Survey Engine...${NC}"

# Function to kill existing processes
kill_existing_processes() {
    echo -e "${YELLOW}🛑 Cleaning up existing processes...${NC}"
    
    # Kill any existing nginx processes (check both common ports)
    if pgrep -f "nginx" > /dev/null; then
        pkill -f "nginx" || true
        sleep 1
    fi
    
    # Kill any existing FastAPI/uvicorn processes
    if pgrep -f "uvicorn" > /dev/null; then
        pkill -f "uvicorn" || true
        sleep 1
    fi
    
    # Kill any processes using port 3000 (nginx)
    if lsof -ti:3000 > /dev/null 2>&1; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # Kill any processes using port 8000 (FastAPI)
    if lsof -ti:8000 > /dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    echo -e "${GREEN}✅ Existing processes cleaned up${NC}"
}

# Function to check port availability
check_port_availability() {
    echo -e "${YELLOW}🔍 Checking port availability...${NC}"
    
    # Check port 4321
    if lsof -ti:4321 > /dev/null 2>&1; then
        echo -e "${RED}❌ Port 4321 is still in use${NC}"
        echo -e "${YELLOW}💡 Try running: lsof -ti:4321 | xargs kill -9${NC}"
        exit 1
    fi
    
    # Check port 8000
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo -e "${RED}❌ Port 8000 is still in use${NC}"
        echo -e "${YELLOW}💡 Try running: lsof -ti:8000 | xargs kill -9${NC}"
        exit 1
    fi
    
    
    echo -e "${GREEN}✅ Ports 4321 and 8000 are available${NC}"
}

# Function to check environment variables
check_environment() {
    echo -e "${YELLOW}🔍 Checking environment configuration...${NC}"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  No .env file found${NC}"
        if [ -f ".env.example" ]; then
            echo -e "${BLUE}💡 Copy .env.example to .env and configure your API tokens:${NC}"
            echo -e "${CYAN}   cp .env.example .env${NC}"
            echo -e "${CYAN}   nano .env${NC}"
        else
            echo -e "${BLUE}💡 Create a .env file with your API tokens:${NC}"
            echo -e "${CYAN}   echo 'REPLICATE_API_TOKEN=your_token_here' > .env${NC}"
        fi
        echo -e "${YELLOW}⚠️  Continuing without API token - RFQ features will not work${NC}"
    else
        echo -e "${GREEN}✅ .env file found${NC}"
        
        # Check if REPLICATE_API_TOKEN is set
        if [ -z "$REPLICATE_API_TOKEN" ]; then
            echo -e "${YELLOW}⚠️  REPLICATE_API_TOKEN not set in environment${NC}"
            echo -e "${BLUE}💡 Add REPLICATE_API_TOKEN to your .env file:${NC}"
            echo -e "${CYAN}   echo 'REPLICATE_API_TOKEN=your_token_here' >> .env${NC}"
            echo -e "${YELLOW}⚠️  RFQ features will not work without this token${NC}"
        else
            echo -e "${GREEN}✅ REPLICATE_API_TOKEN is configured${NC}"
        fi
    fi
    
    echo -e "${BLUE}📋 Environment check completed${NC}"
}

# Function to check if database is ready
check_database() {
    echo -e "${YELLOW}🔍 Checking database connection...${NC}"
    
    # Set default DATABASE_URL if not provided
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️  No DATABASE_URL found, using default local development settings${NC}"
        export DATABASE_URL="postgresql://chaitanya@localhost:5432/survey_engine_db"
        export REDIS_URL="redis://127.0.0.1:6379"
    fi
    
    # Try to connect to database
    echo -e "${BLUE}🔍 Testing connection to: $DATABASE_URL${NC}"
    if DATABASE_URL="$DATABASE_URL" uv run python3 -c "
import os
import psycopg2
from urllib.parse import urlparse

try:
    url = os.getenv('DATABASE_URL')
    if not url:
        print('No DATABASE_URL found')
        exit(1)
    
    parsed = urlparse(url)
    print(f'Connecting to: {parsed.hostname}:{parsed.port} database: {parsed.path[1:]} user: {parsed.username}')
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
        echo -e "${YELLOW}💡 Make sure Docker containers are running:${NC}"
        echo -e "${YELLOW}   docker-compose -f docker-compose.dev.yml up -d postgres redis${NC}"
        exit 1
    fi
}

# Function to run database migrations via API
run_migrations() {
    echo -e "${YELLOW}📊 Running database bootstrap via migrate-all (idempotent)...${NC}"
    
    # Start FastAPI server temporarily for migrations
    REPLICATE_API_TOKEN="$REPLICATE_API_TOKEN" DATABASE_URL="$DATABASE_URL" uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    MIGRATION_PID=$!
    
    # Wait for server to be ready
    sleep 5
    
    # Check if server is running
    if ! kill -0 $MIGRATION_PID 2>/dev/null; then
        echo -e "${RED}❌ FastAPI failed to start for migrations${NC}"
        return 1
    fi
    
    # Wait for server to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ FastAPI is ready for migrations${NC}"
            break
        fi
        # Silent wait - only show if it takes too long
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ FastAPI failed to become ready for migrations${NC}"
        kill $MIGRATION_PID 2>/dev/null || true
        return 1
    fi
    
    # Run migrations via API (now calls bootstrap internally)
    echo -e "${BLUE}📝 Executing migrations (bootstrap)...${NC}"
    local migration_result
    migration_result=$(curl -s -X POST "http://localhost:8000/api/v1/admin/migrate-all" -H "Content-Type: application/json")
    
    # Stop the temporary server
    kill $MIGRATION_PID 2>/dev/null || true
    sleep 2
    
    # Check migration result
    if echo "$migration_result" | grep -q '"status":"success"'; then
        echo -e "${GREEN}✅ Database migrations (bootstrap) completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Database migrations failed${NC}"
        echo -e "${RED}Migration result: $migration_result${NC}"
        return 1
    fi
}

# Function to seed the database

# Function to start the application
start_application() {
    echo -e "${YELLOW}🚀 Starting application...${NC}"
    
    # Check if we're in Railway (has RAILWAY_ENVIRONMENT) or local development
    if [ -n "$RAILWAY_ENVIRONMENT" ]; then
        echo -e "${BLUE}🏗️  Starting in production mode (Railway)${NC}"
        echo -e "${BLUE}   - Nginx will run on port $APP_PORT${NC}"
        echo -e "${BLUE}   - FastAPI will run on port $FASTAPI_PORT${NC}"
        
        # Start the consolidated application
        DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" ./start.sh consolidated
    else
        echo -e "${BLUE}🏠 Starting in development mode (Local without Docker)${NC}"
        
        # For local development, start both FastAPI and React production build
        echo -e "${BLUE}   - FastAPI will run on port 8000${NC}"
        echo -e "${BLUE}   - React app will run on port 3000 (production build)${NC}"
        
        # Set environment variables for local development
        export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN}"
        export DATABASE_URL="${DATABASE_URL:-postgresql://chaitanya@localhost:5432/survey_engine_db}"
        
        # Start FastAPI in background
        echo -e "${YELLOW}🔄 Starting FastAPI server...${NC}"
        REPLICATE_API_TOKEN="$REPLICATE_API_TOKEN" DATABASE_URL="$DATABASE_URL" uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
        FASTAPI_PID=$!
        
        # Wait for FastAPI to be ready
        sleep 5
        
        # Check if FastAPI is running
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ FastAPI is running on port 8000${NC}"
        else
            echo -e "${RED}❌ FastAPI failed to start${NC}"
            exit 1
        fi
        
        # Nginx is already running from early startup
        echo -e "${GREEN}✅ Nginx already running and serving frontend on port 3000${NC}"
        
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        echo -e "${GREEN}   - Frontend: http://localhost:3000${NC}"
        echo -e "${GREEN}   - API: http://localhost:8000${NC}"
        echo -e "${GREEN}   - API Health: http://localhost:8000/health${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        
        # Function to handle shutdown
        cleanup() {
            echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
            
            # Kill by PID if available
            if [ ! -z "$NGINX_PID" ]; then
                kill $NGINX_PID 2>/dev/null || true
                echo -e "${GREEN}✅ Nginx stopped (PID: $NGINX_PID)${NC}"
            fi
            if [ ! -z "$FASTAPI_PID" ]; then
                kill $FASTAPI_PID 2>/dev/null || true
                echo -e "${GREEN}✅ FastAPI stopped (PID: $FASTAPI_PID)${NC}"
            fi
            
            # Force kill any remaining processes on our ports
            if lsof -ti:8000 > /dev/null 2>&1; then
                echo -e "${YELLOW}🔄 Force killing remaining processes on port 8000...${NC}"
                lsof -ti:8000 | xargs kill -9 2>/dev/null || true
            fi
            
            echo -e "${GREEN}✅ All services stopped${NC}"
            exit 0
        }
        
        # Set up signal handlers
        trap cleanup SIGTERM SIGINT
        
        # Wait for any process to exit
        wait $NGINX_PID $FASTAPI_PID
    fi
}

# Function to run quick smoke tests
run_quick_tests() {
    echo -e "${YELLOW}🧪 Running quick smoke tests...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ Error: pyproject.toml not found. Please run from project root.${NC}"
        exit 1
    fi
    
    # Install development dependencies if not already installed
    echo -e "${BLUE}📦 Installing development dependencies...${NC}"
    if ! uv sync --dev; then
        echo -e "${RED}❌ Failed to install development dependencies${NC}"
        exit 1
    fi
    
    # Run critical tests only (fast subset)
    if ./scripts/run_tests.sh critical --quiet; then
        echo -e "${GREEN}✅ Smoke tests passed${NC}"
    else
        echo -e "${RED}❌ Smoke tests failed${NC}"
        echo -e "${YELLOW}💡 Run full tests: ./scripts/run_tests.sh all${NC}"
        exit 1
    fi
}

# Function to run full test suite
run_full_tests() {
    echo -e "${YELLOW}🧪 Running full test suite...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ Error: pyproject.toml not found. Please run from project root.${NC}"
        exit 1
    fi
    
    # Install development dependencies if not already installed
    echo -e "${BLUE}📦 Installing development dependencies...${NC}"
    if ! uv sync --dev; then
        echo -e "${RED}❌ Failed to install development dependencies${NC}"
        exit 1
    fi
    
    # Run all tests
    if ./scripts/run_tests.sh all; then
        echo -e "${GREEN}✅ All tests passed${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

# Function to run tests with coverage
run_tests_with_coverage() {
    echo -e "${YELLOW}🧪 Running tests with coverage...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ Error: pyproject.toml not found. Please run from project root.${NC}"
        exit 1
    fi
    
    # Install development dependencies if not already installed
    echo -e "${BLUE}📦 Installing development dependencies...${NC}"
    if ! uv sync --dev; then
        echo -e "${RED}❌ Failed to install development dependencies${NC}"
        exit 1
    fi
    
    # Run tests with coverage
    if ./scripts/run_tests.sh all --coverage; then
        echo -e "${GREEN}✅ Tests with coverage completed${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

# Function to run development checks
run_dev_checks() {
    echo -e "${YELLOW}🔍 Running development checks...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ Error: pyproject.toml not found. Please run from project root.${NC}"
        exit 1
    fi
    
    # Install development dependencies if not already installed
    echo -e "${BLUE}📦 Installing development dependencies...${NC}"
    if ! uv sync --dev; then
        echo -e "${RED}❌ Failed to install development dependencies${NC}"
        exit 1
    fi
    
    # Run quick smoke tests first
    echo -e "${BLUE}🧪 Running quick smoke tests...${NC}"
    if ./scripts/run_tests.sh critical --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Smoke tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Smoke tests failed, but continuing with other checks...${NC}"
    fi
    
    # Run logger usage check
    if ! uv run python scripts/check_logger_usage.py > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Logger usage check found issues${NC}"
    else
        echo -e "${GREEN}✅ Logger usage check passed${NC}"
    fi
    
    # Run formatting check
    if ! uv run black --check src/ > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Code formatting issues found${NC}"
    else
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    fi
    
    # Run import sorting check
    if ! uv run isort --check-only src/ > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Import sorting issues found${NC}"
    else
        echo -e "${GREEN}✅ Import sorting is correct${NC}"
    fi
    
    echo -e "${GREEN}✅ Development checks completed${NC}"
}

# Function to start nginx early for immediate frontend access
start_nginx_early() {
    echo -e "${YELLOW}🔄 Building React application...${NC}"
    cd frontend && npm run build
    cd ..
    
    echo -e "${YELLOW}🔄 Starting nginx early...${NC}"
    nginx -c $(pwd)/nginx-local.conf &
    NGINX_PID=$!
    
    # Wait for nginx to be ready
    sleep 3
    
    # Check if nginx is responding (more reliable than PID check)
    local max_attempts=5
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Nginx is running and serving frontend on port 3000${NC}"
            break
        fi
        echo -e "${YELLOW}⏳ Waiting for nginx... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo -e "${RED}❌ Nginx failed to start or respond${NC}"
        echo -e "${YELLOW}Checking nginx processes...${NC}"
        ps aux | grep nginx | grep -v grep
        exit 1
    fi
}

# Function to preload models (deprecated - now handled by FastAPI startup)
preload_models() {
    echo -e "${BLUE}🧠 Model preloading is now handled by FastAPI startup${NC}"
    echo -e "${BLUE}   Models will load in background after server starts${NC}"
    return 0
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Starting Survey Engine...${NC}"
    
    # Load environment variables
    if [ -f ".env" ]; then
        echo -e "${BLUE}📄 Loading environment variables from .env${NC}"
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Always clean up existing processes first
    kill_existing_processes
    
    # Check prerequisites
    check_port_availability
    check_environment
    
    # Start nginx early (frontend available immediately)
    if [ -z "$RAILWAY_ENVIRONMENT" ]; then
        echo -e "${YELLOW}🔄 Starting nginx early for immediate frontend access...${NC}"
        start_nginx_early
    fi
    
    # Check database and setup
    check_database

    # Database setup is manual - show instructions
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📋 Database Setup (Manual):${NC}"
    echo -e "${CYAN}   First time? Run: ./start-local.sh migrate${NC}"
    echo -e "${CYAN}   Need data? Run: python migrations/seed_core_generation_rules.py${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Run development checks (only in local development)
    if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$PORT" ]; then
        run_dev_checks
    fi
    
    # Preload models (in background)
    preload_models &
    
    # Start application
    start_application
}

# Handle command line arguments
case "${1:-startup}" in
    "startup")
        main
        ;;
    "startup-safe")
        # Run tests first, only start if tests pass
        run_quick_tests || exit 1
        main
        ;;
    "migrate")
        check_database
        run_migrations
        ;;
    "preload")
        preload_models
        ;;
    "dev-checks")
        run_dev_checks
        ;;
    "test-quick")
        run_quick_tests
        ;;
    "test-full")
        run_full_tests
        ;;
    "test-coverage")
        run_tests_with_coverage
        ;;
    "kill")
        kill_existing_processes
        ;;
    "setup-env")
        if [ -f ".env.example" ]; then
            if [ ! -f ".env" ]; then
                cp .env.example .env
                echo -e "${GREEN}✅ Created .env file from .env.example${NC}"
                echo -e "${YELLOW}⚠️  Please edit .env and add your REPLICATE_API_TOKEN${NC}"
                echo -e "${CYAN}   nano .env${NC}"
            else
                echo -e "${YELLOW}⚠️  .env file already exists${NC}"
            fi
        else
            echo -e "${RED}❌ .env.example file not found${NC}"
        fi
        ;;
    "help")
        echo "Survey Engine Startup Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  startup       - Start server (no auto database ops)"
        echo "  startup-safe  - Run tests first, then start"
        echo "  migrate       - Run database bootstrap (idempotent)"
        echo "  dev-checks    - Run development checks"
        echo "  test-quick    - Run quick smoke tests"
        echo "  test-full     - Run full test suite"
        echo "  test-coverage - Run tests with coverage"
        echo "  kill          - Kill existing processes"
        echo "  setup-env     - Create .env file"
        echo "  help          - Show this help"
        echo ""
        echo "Database:"
        echo "  ./start-local.sh migrate  - Bootstrap schema"
        echo "  python migrations/seed_core_generation_rules.py  - Seed rules"
        echo "  python scripts/populate_rule_based_multi_level_rag.py  - Seed RAG"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
