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

# Function to run migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_info "Skipping database migrations (SKIP_MIGRATIONS=true)"
        return 0
    fi
    
    log_info "Running database migrations..."
    log_info "Alembic command: $UV_CMD run alembic upgrade head"
    log_info "Current working directory: $(pwd)"
    log_info "Alembic files: $(ls -la alembic/)"
    
    # Try to run migrations with detailed error output
    log_info "Executing migration command..."
    if $UV_CMD run alembic upgrade head 2>&1; then
        log_success "Database migrations completed successfully"
    else
        local exit_code=$?
        log_error "Database migrations failed with exit code $exit_code"
        log_info "Continuing anyway..."
        return 0
    fi
}

# Function to start FastAPI server
start_fastapi() {
    local port=${PORT:-8000}
    log_info "Starting FastAPI server on port $port..."
    
    if [ "$DEBUG" = "true" ]; then
        if ! $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --reload --timeout-keep-alive 600; then
            log_error "Failed to start FastAPI server in debug mode"
            exit 1
        fi
    else
        if ! $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 600; then
            log_error "Failed to start FastAPI server"
            exit 1
        fi
    fi
}

# Function to start WebSocket server
start_websocket() {
    local port=${PORT:-8001}
    log_info "Starting WebSocket server on port $port..."
    if ! $UV_CMD run python3 websocket_server.py; then
        log_error "Failed to start WebSocket server"
        exit 1
    fi
}

# Function to generate nginx config with dynamic port
generate_nginx_config() {
    local nginx_port=${PORT:-80}
    log_info "Generating nginx config for port $nginx_port"
    
    cat > /etc/nginx/nginx.conf << EOF
user app;
worker_processes auto;
pid /app/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    sendfile on;
    keepalive_timeout 65;
    
    # Global timeout settings for ML model loading
    proxy_connect_timeout       600s;
    proxy_send_timeout          600s;
    proxy_read_timeout          600s;
    send_timeout               600s;
    
    server {
        listen $nginx_port;
        server_name _;
        root /app/frontend/build;
        index index.html;

        # Serve React app
        location / {
            try_files \$uri \$uri/ /index.html;
        }

        # API health check - direct proxy to FastAPI
        location = /api/health {
            proxy_pass http://127.0.0.1:8001/health;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # All API routes to FastAPI server
        location /api/ {
            proxy_pass http://127.0.0.1:8000/api/v1/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header Connection "";
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_cache off;
            # Increase timeouts for ML model loading
            proxy_connect_timeout       600s;
            proxy_send_timeout          600s;
            proxy_read_timeout          600s;
        }

        # WebSocket proxy
        location /ws/ {
            proxy_pass http://127.0.0.1:8001/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Health check endpoint - proxy to FastAPI (exact match)
        location = /health {
            proxy_pass http://127.0.0.1:8001/health;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
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
    log_info "FastAPI command: $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 600"
    
    # Start FastAPI and capture output for debugging
    log_info "Starting FastAPI with command: $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 600"
    
    if [ "$DEBUG" = "true" ]; then
        $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --reload --timeout-keep-alive 600 2>&1 | tee /tmp/fastapi.log &
    else
        $UV_CMD run uvicorn src.main:app --host 0.0.0.0 --port $port --timeout-keep-alive 600 2>&1 | tee /tmp/fastapi.log &
    fi
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
            log_info "Curl verbose output:"
            curl -v http://localhost:8000/health 2>&1 || true
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
        sleep 3  # Increased sleep time
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "FastAPI server failed to become ready after $max_attempts attempts"
        log_error "This might be due to ML model loading taking too long"
        exit 1
    fi
    
    # Start WebSocket server in background
    log_info "Starting WebSocket server..."
    local ws_port=8001
    log_info "WebSocket command: $UV_CMD run python3 websocket_server.py"
    
    $UV_CMD run python3 websocket_server.py &
    WEBSOCKET_PID=$!
    log_success "WebSocket server started with PID $WEBSOCKET_PID"
    
    # Check if WebSocket started successfully
    log_info "Checking if WebSocket process is running..."
    sleep 2
    if ! kill -0 $WEBSOCKET_PID 2>/dev/null; then
        log_error "WebSocket server failed to start (PID $WEBSOCKET_PID not running)"
        exit 1
    fi
    
    # Wait for WebSocket to be ready (readiness check) - doesn't depend on ML models
    log_info "Waiting for WebSocket to be ready..."
    local max_attempts=20  # Reduced timeout since we don't wait for ML models
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8001/ready > /dev/null 2>&1; then
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
    
    # Add debug information
    log_info "Python version: $(python3 --version)"
    log_info "UV version: $(uv --version)"
    log_info "Working directory: $(pwd)"
    log_info "Available files: $(ls -la)"
    
    # Test Python imports
    log_info "Testing Python imports..."
    if python3 -c "import sys; print('Python path:', sys.path)"; then
        log_success "Python basic test passed"
    else
        log_error "Python basic test failed"
        exit 1
    fi
    
    # Test if we can import the main modules
    log_info "Testing module imports..."
    if python3 -c "import src.main; print('src.main imported successfully')"; then
        log_success "src.main import test passed"
    else
        log_error "src.main import test failed"
        exit 1
    fi
    
    # Wait for dependencies
    log_info "Step 1: Waiting for database..."
    wait_for_db || exit 1
    
    log_info "Step 2: Checking Redis..."
    check_redis || true  # Redis is optional, don't exit if unavailable
    
    log_info "Step 3: Running migrations..."
    run_migrations || exit 1
    
    log_info "Step 4: Starting services..."
    
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
