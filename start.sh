#!/bin/bash
set -e

# UV should be available in /usr/local/bin
UV_CMD="uv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for database
wait_for_db() {
    log_info "Waiting for database at ${DATABASE_HOST:-localhost}:${DATABASE_PORT:-5432}..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h ${DATABASE_HOST:-localhost} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-survey_engine} > /dev/null 2>&1; then
            log_success "Database is ready!"
            return 0
        fi
        
        log_warning "Database is unavailable - attempt $attempt/$max_attempts"
        sleep 2
        ((attempt++))
    done
    
    log_error "Database connection failed after $max_attempts attempts"
    return 1
}

# Function to wait for Redis
wait_for_redis() {
    log_info "Waiting for Redis at ${REDIS_URL:-redis://localhost:6379}..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if redis-cli -u ${REDIS_URL:-redis://localhost:6379} ping > /dev/null 2>&1; then
            log_success "Redis is ready!"
            return 0
        fi
        
        log_warning "Redis is unavailable - attempt $attempt/$max_attempts"
        sleep 2
        ((attempt++))
    done
    
    log_error "Redis connection failed after $max_attempts attempts"
    return 1
}

# Function to run migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_info "Skipping database migrations (SKIP_MIGRATIONS=true)"
        return 0
    fi
    
    log_info "Running database migrations..."
    if $UV_CMD run alembic upgrade head; then
        log_success "Database migrations completed successfully"
    else
        log_warning "Database migrations failed, but continuing..."
        return 0
    fi
}

# Function to start FastAPI server
start_fastapi() {
    local port=${PORT:-8000}
    log_info "Starting FastAPI server on port $port..."
    
    if [ "$DEBUG" = "true" ]; then
        $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --reload
    else
        $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port
    fi
}

# Function to start WebSocket server
start_websocket() {
    local port=${PORT:-8001}
    log_info "Starting WebSocket server on port $port..."
    $UV_CMD run python3 websocket_server.py
}

# Function to start both services
start_both() {
    log_info "Starting both FastAPI and WebSocket servers..."
    
    # Start FastAPI in background
    start_fastapi &
    FASTAPI_PID=$!
    log_success "FastAPI server started with PID $FASTAPI_PID"
    
    # Wait a moment for FastAPI to start
    sleep 3
    
    # Start WebSocket server in background
    start_websocket &
    WEBSOCKET_PID=$!
    log_success "WebSocket server started with PID $WEBSOCKET_PID"
    
    # Function to handle shutdown
    cleanup() {
        log_info "Shutting down services..."
        if [ ! -z "$FASTAPI_PID" ]; then
            kill $FASTAPI_PID 2>/dev/null || true
            log_info "FastAPI server stopped"
        fi
        if [ ! -z "$WEBSOCKET_PID" ]; then
            kill $WEBSOCKET_PID 2>/dev/null || true
            log_info "WebSocket server stopped"
        fi
        exit 0
    }
    
    # Set up signal handlers
    trap cleanup SIGTERM SIGINT
    
    log_success "Both services are running. Press Ctrl+C to stop."
    
    # Wait for either process to exit
    wait $FASTAPI_PID $WEBSOCKET_PID
}

# Main execution
main() {
    log_info "Starting Survey Engine..."
    log_info "Service: ${SERVICE:-'both'}"
    log_info "Debug mode: ${DEBUG:-'false'}"
    
    # Wait for dependencies
    wait_for_db || exit 1
    wait_for_redis || exit 1
    
    # Run migrations
    run_migrations || exit 1
    
    # Start the appropriate service(s)
    case "${SERVICE:-both}" in
        "backend")
            start_fastapi
            ;;
        "websocket")
            start_websocket
            ;;
        "both"|"")
            start_both
            ;;
        *)
            log_error "Unknown service: $SERVICE"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
