#!/bin/bash
# set -e  # Removed to allow graceful handling of optional services

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
    # Parse DATABASE_URL if provided
    if [ -n "$DATABASE_URL" ]; then
        # Extract host, port, and user from DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        
        # Use parsed values or defaults
        local host=${db_host:-${DATABASE_HOST:-localhost}}
        local port=${db_port:-${DATABASE_PORT:-5432}}
        local user=${db_user:-${DATABASE_USER:-survey_engine}}
    else
        # Use individual environment variables
        local host=${DATABASE_HOST:-localhost}
        local port=${DATABASE_PORT:-5432}
        local user=${DATABASE_USER:-survey_engine}
    fi
    
    log_info "Waiting for database at ${host}:${port}..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h "$host" -p "$port" -U "$user" > /dev/null 2>&1; then
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

# Function to check Redis availability (optional)
check_redis() {
    if [ -n "$REDIS_URL" ] && [ "$REDIS_URL" != "" ]; then
        log_info "Checking Redis at ${REDIS_URL}..."
        # Check if redis-cli is available first
        if command -v redis-cli > /dev/null 2>&1; then
            if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
                log_success "Redis is available!"
                return 0
            else
                log_warning "Redis is unavailable - continuing without caching"
                return 1
            fi
        else
            log_warning "redis-cli not available - continuing without Redis"
            return 1
        fi
    else
        log_info "No Redis URL provided - running without caching"
        return 1
    fi
}

# Function to run migrations via API
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_info "Skipping database migrations (SKIP_MIGRATIONS=true)"
        return 0
    fi
    
    log_info "Running database migrations using admin API..."
    log_info "Current working directory: $(pwd)"
    
    # Start FastAPI server temporarily for migrations
    log_info "Starting FastAPI server for migrations..."
    $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    local migration_pid=$!
    
    # Wait for server to be ready
    log_info "Waiting for FastAPI to be ready..."
    sleep 5
    
    # Check if server is running
    if ! kill -0 $migration_pid 2>/dev/null; then
        log_error "FastAPI failed to start for migrations"
        return 1
    fi
    
    # Wait for server to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "FastAPI is ready for migrations"
            break
        fi
        log_info "Waiting for FastAPI... (attempt $((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "FastAPI failed to become ready for migrations"
        kill $migration_pid 2>/dev/null || true
        return 1
    fi
    
    # Run migrations via API
    log_info "Executing migrations via API..."
    local migration_result
    migration_result=$(curl -s -X POST "http://localhost:8000/api/v1/admin/migrate-all" -H "Content-Type: application/json")
    
    # Stop the temporary server
    log_info "Stopping temporary FastAPI server..."
    kill $migration_pid 2>/dev/null || true
    sleep 2
    
    # Check migration result
    if echo "$migration_result" | grep -q '"status":"success"'; then
        log_success "Database migrations completed successfully"
        return 0
    else
        log_error "Database migrations failed"
        log_error "Migration result: $migration_result"
        return 1
    fi
}

# Global flag to track if models are already preloaded
MODELS_PRELOADED=false

# Function to preload models (deprecated - now handled by FastAPI startup)
preload_models() {
    log_info "Model preloading is now handled by FastAPI startup - skipping standalone preload"
    log_info "Models will load in background after server starts"
    return 0
}

# Function to start FastAPI server
start_fastapi() {
    local port=${PORT:-8000}
    log_info "Starting FastAPI server on port $port..."
    
    # Manual deployment only - no auto-reload
    if ! $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 900; then
        log_error "Failed to start FastAPI server"
        exit 1
    fi
}

start_nginx() {
    log_info "Starting nginx server..."
    
    # Generate nginx config
    generate_nginx_config
    
    # Start nginx in foreground
    if ! nginx -g "daemon off;"; then
        log_error "Failed to start nginx"
        exit 1
    fi
}

start_consolidated() {
    local fastapi_port=8000
    local nginx_port=${PORT:-8080}
    log_info "Starting consolidated FastAPI + nginx server..."
    
    # Step 1: Start nginx in background
    log_info "🔄 Step 1: Starting nginx on port $nginx_port..."
    generate_nginx_config
    nginx -g "daemon on;" || {
        log_error "Failed to start nginx"
        exit 1
    }
    
    # Wait for nginx to be ready (check if nginx is responding on port)
    log_info "⏳ Waiting for nginx to be ready..."
    local max_attempts=10
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        # Check if nginx process is running AND responding on the port
        if pgrep nginx > /dev/null 2>&1 && curl -s -f "http://localhost:$nginx_port/health" > /dev/null 2>&1; then
            log_success "✅ Step 1: Nginx is ready and responding on port $nginx_port!"
            break
        fi
        log_info "Nginx not ready yet - attempt $attempt/$max_attempts"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_warning "Nginx readiness check timed out, but continuing..."
        # Try to start nginx if it's not running
        if ! pgrep nginx > /dev/null 2>&1; then
            log_info "Attempting to start nginx..."
            nginx -c /etc/nginx/nginx.conf &
            sleep 3
        fi
    fi
    
    # Step 2: Start FastAPI in foreground
    log_info "🔄 Step 2: Starting FastAPI server on port $fastapi_port..."
    log_success "🚀 All services ready! Starting FastAPI..."
    # Manual deployment only - no auto-reload
    $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port $fastapi_port --timeout-keep-alive 900
}

# Function to start WebSocket server
start_websocket() {
    local port=${PORT:-8000}
    log_info "Starting WebSocket server on port $port..."
    # WebSocket functionality is now integrated into the main FastAPI app (src/main.py)
    log_info "WebSocket support is available through the main FastAPI server"
}

# Function to generate nginx config with dynamic port
generate_nginx_config() {
    local nginx_port=${PORT:-80}
    log_info "Generating nginx config for port $nginx_port"
    
    printf 'user app;\nworker_processes auto;\npid /app/nginx.pid;\n\nevents {\n    worker_connections 1024;\n}\n\nhttp {\n    include /etc/nginx/mime.types;\n    default_type application/octet-stream;\n    \n    sendfile on;\n    keepalive_timeout 65;\n    \n    # Global timeout settings for ML model loading\n    proxy_connect_timeout       900s;\n    proxy_send_timeout          900s;\n    proxy_read_timeout          900s;\n    send_timeout               900s;\n    \n    server {\n        listen %s;\n        server_name _;\n        root /app/frontend/build;\n        index index.html;\n\n        # Serve React app\n        location / {\n            try_files $uri $uri/ /index.html;\n        }\n\n        # API health check - direct proxy to FastAPI\n        location = /api/health {\n            proxy_pass http://127.0.0.1:8000/health;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n\n        # All API routes to FastAPI server\n        location /api/ {\n            proxy_pass http://127.0.0.1:8000;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n            proxy_set_header Connection "";\n            proxy_http_version 1.1;\n            proxy_buffering off;\n            proxy_cache off;\n            # Increase timeouts for ML model loading\n            proxy_connect_timeout       900s;\n            proxy_send_timeout          900s;\n            proxy_read_timeout          900s;\n        }\n\n        # WebSocket proxy to FastAPI server (consolidated)\n        location /ws/ {\n            proxy_pass http://127.0.0.1:8000/ws/;\n            proxy_http_version 1.1;\n            proxy_set_header Upgrade $http_upgrade;\n            proxy_set_header Connection "upgrade";\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n\n        # Health check endpoint - proxy to FastAPI (exact match)\n        location = /health {\n            proxy_pass http://127.0.0.1:8000/health;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n    }\n}\n' "$nginx_port" > /etc/nginx/nginx.conf
    log_success "Generated nginx config for port $nginx_port"
}

# Function to start nginx
start_nginx() {
    log_info "Starting nginx web server..."
    
    # Generate nginx config with correct port
    generate_nginx_config
    
    # Test nginx configuration first
    log_info "Testing nginx configuration..."
    if ! nginx -t 2>/dev/null; then
        log_error "Nginx configuration test failed"
        nginx -t  # Show the error
        exit 1
    fi
    log_success "Nginx configuration is valid"
    
    # Start nginx in foreground mode
    log_info "Starting nginx..."
    nginx -g "daemon off;" &
    NGINX_PID=$!
    log_success "Nginx started with PID $NGINX_PID"
    
    # Check if nginx started successfully
    sleep 2
    if ! kill -0 $NGINX_PID 2>/dev/null; then
        log_error "Nginx failed to start (PID $NGINX_PID not running)"
        exit 1
    fi
    log_success "Nginx is running successfully on port ${PORT:-80}"
}

# Function to start both services
start_both() {
    log_info "Starting FastAPI, WebSocket, and nginx servers..."
    
    # Start FastAPI in background
    log_info "Starting FastAPI server..."
    local port=8000
    log_info "FastAPI command: $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 900"
    
    # Start FastAPI and capture output for debugging
    log_info "Starting FastAPI with command: $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 900"
    
    # Manual deployment only - no auto-reload
    $UV_CMD run --no-project uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 900 > /tmp/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    log_success "FastAPI server started with PID $FASTAPI_PID"
    
    # Show initial FastAPI output
    sleep 3
    log_info "FastAPI initial output:"
    if [ -f /tmp/fastapi.log ]; then
        log_info "FastAPI log file exists, showing content:"
        cat /tmp/fastapi.log
    else
        log_error "FastAPI log file not created!"
    fi
    
    # Check if FastAPI started successfully and is ready
    log_info "Checking if FastAPI process is running..."
    sleep 2
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        log_error "FastAPI server failed to start (PID $FASTAPI_PID not running)"
        log_error "FastAPI error log:"
        if [ -f /tmp/fastapi.log ]; then
            cat /tmp/fastapi.log
        else
            log_error "No FastAPI log file found"
        fi
        exit 1
    fi
    
    # Wait for FastAPI to be ready (health check)
    log_info "Waiting for FastAPI to be ready..."
    local max_attempts=60  # Increased timeout for ML model loading
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts: curl -f http://localhost:8000/health"
        if curl -f http://localhost:8000/health 2>&1; then
            log_success "FastAPI server is ready!"
            break
        else
            local curl_exit_code=$?
            log_warning "Health check failed with exit code $curl_exit_code"
            # Show what curl actually sees
            log_info "FastAPI process status:"
            if kill -0 $FASTAPI_PID 2>/dev/null; then
                log_info "FastAPI process $FASTAPI_PID is still running"
            else
                log_error "FastAPI process $FASTAPI_PID has died!"
                log_info "Final FastAPI log output:"
                if [ -f /tmp/fastapi.log ]; then
                    cat /tmp/fastapi.log
                else
                    log_error "No FastAPI log available"
                fi
                exit 1
            fi
        fi
        sleep 3
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "FastAPI server failed to become ready after $max_attempts attempts"
        if [ -f /tmp/fastapi.log ]; then
            log_error "Last 20 lines of FastAPI log:"
            tail -20 /tmp/fastapi.log
        fi
        exit 1
    fi
    
    # WebSocket functionality is now integrated into the main FastAPI app
    log_info "WebSocket support is available through the main FastAPI server at /ws/"
    
    # Wait for WebSocket to be ready (readiness check) - doesn't depend on ML models
    log_info "Waiting for WebSocket to be ready..."
    local max_attempts=20  # Reduced timeout since we don't wait for ML models
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/ready > /dev/null 2>&1; then
            log_success "WebSocket server is ready!"
            break
        fi
        log_info "WebSocket not ready yet - attempt $attempt/$max_attempts"
        sleep 2  # Reduced sleep time
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "WebSocket server failed to become ready after $max_attempts attempts"
        log_error "This might be due to ML model loading taking too long"
        exit 1
    fi
    
    # Start nginx
    start_nginx
    
    # Function to handle shutdown
    cleanup() {
        log_info "Shutting down services..."
        if [ ! -z "$NGINX_PID" ]; then
            kill $NGINX_PID 2>/dev/null || true
            log_info "Nginx server stopped"
        fi
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
    
    log_success "All services are running. Press Ctrl+C to stop."
    
    # Wait for any process to exit
    wait $NGINX_PID $FASTAPI_PID $WEBSOCKET_PID
}

# Main execution
main() {
    log_info "Starting Survey Engine..."
    log_info "Service: ${SERVICE:-'both'}"
    log_info "Debug mode: ${DEBUG:-'false'}"
    
    # Test Python imports using uv with --no-project flag (uses system Python with installed packages)
    if ! $UV_CMD run --no-project python -c "import src.main" > /dev/null 2>&1; then
        log_error "Failed to import src.main - check Python environment"
        log_error "Attempting to show import error details:"
        $UV_CMD run --no-project python -c "import src.main" 2>&1 || true
        exit 1
    fi
    
    # Wait for dependencies
    log_info "Step 1: Waiting for database..."
    wait_for_db || exit 1
    
    log_info "Step 2: Checking Redis..."
    check_redis || true  # Redis is optional, don't exit if unavailable
    
    log_info "Step 3: Database setup (manual)"
    # Database migrations are now manual - run via API when needed
    log_info "To run migrations: curl -X POST 'http://localhost:8000/api/v1/admin/migrate-all'"
    
    log_info "Step 4: Starting services..."
    
    # Start the appropriate service(s)
    case "${SERVICE:-consolidated}" in
        "backend"|"fastapi")
            start_fastapi
            ;;
        "nginx")
            start_nginx
            ;;
        "websocket")
            log_warning "WebSocket server is now integrated into FastAPI. Starting consolidated server instead."
            start_consolidated
            ;;
        "both"|"consolidated"|"")
            log_info "Starting consolidated FastAPI + nginx server (includes WebSocket support)"
            start_consolidated
            ;;
        *)
            log_error "Unknown service: $SERVICE"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
