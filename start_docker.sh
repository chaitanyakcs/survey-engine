#!/bin/bash
# Docker-optimized startup script for Survey Engine
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Global flag to track if models are already preloaded
MODELS_PRELOADED=false

# Function to preload models (Docker-optimized)
preload_models() {
    if [ "$MODELS_PRELOADED" = true ]; then
        log_info "Models already preloaded, skipping..."
        return 0
    fi
    
    log_info "Preloading ML models (Docker-optimized)..."
    
    # Use optimized preloader if available
    if [ -f "preload_models_optimized.py" ]; then
        if python3 preload_models_optimized.py; then
            log_success "Model preloading completed successfully"
            MODELS_PRELOADED=true
        else
            log_warning "Optimized model preloading failed, trying fallback..."
            if python3 preload_models.py; then
                log_success "Fallback model preloading completed"
                MODELS_PRELOADED=true
            else
                log_warning "All model preloading failed, continuing anyway"
                MODELS_PRELOADED=true
            fi
        fi
    else
        if python3 preload_models.py; then
            log_success "Model preloading completed successfully"
            MODELS_PRELOADED=true
        else
            log_warning "Model preloading failed, but continuing with startup"
            MODELS_PRELOADED=true
        fi
    fi
}

# Function to wait for database (Docker-optimized)
wait_for_database() {
    log_info "Waiting for database connection..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python3 -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/survey_engine'))
    conn.close()
    print('Database connected')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
            log_success "Database is ready!"
            return 0
        else
            log_info "Database not ready yet (attempt $attempt/$max_attempts)..."
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    log_error "Database connection timeout after $max_attempts attempts"
    return 1
}

# Function to run database migrations (Docker-optimized)
run_migrations() {
    log_info "Running database migrations..."
    
    # Run all migrations
    for migration in migrations/*.sql; do
        if [ -f "$migration" ]; then
            log_info "Running migration: $(basename "$migration")"
            if psql "$DATABASE_URL" -f "$migration" > /dev/null 2>&1; then
                log_success "Migration $(basename "$migration") completed"
            else
                log_warning "Migration $(basename "$migration") had issues (continuing...)"
            fi
        fi
    done
    
    log_success "All migrations completed"
}

# Function to generate nginx config (Docker-optimized)
generate_nginx_config() {
    local nginx_port=${PORT:-8080}
    log_info "Generating nginx config for port $nginx_port"
    
    cat > /etc/nginx/nginx.conf << EOF
user app;
worker_processes auto;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    access_log /dev/stdout;
    error_log /dev/stderr;
    
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Upstream configuration
    upstream fastapi_backend {
        server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    server {
        listen $nginx_port;
        server_name _;
        root /app/frontend/build;
        index index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Serve React app
        location / {
            try_files \$uri \$uri/ /index.html;
        }
        
        # API routes with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://fastapi_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header Connection "";
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_cache off;
            
            # Timeouts for ML operations
            proxy_connect_timeout 900s;
            proxy_send_timeout 900s;
            proxy_read_timeout 900s;
        }
        
        # WebSocket support
        location /ws/ {
            proxy_pass http://fastapi_backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # WebSocket timeouts
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }
        
        # Health check
        location = /health {
            proxy_pass http://fastapi_backend/health;
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

# Function to start the application (Docker-optimized)
start_application() {
    log_info "Starting Survey Engine application..."
    
    # Step 1: Wait for database
    wait_for_database
    
    # Step 2: Run migrations
    run_migrations
    
    # Step 3: Preload models
    preload_models
    
    # Step 4: Generate nginx config
    generate_nginx_config
    
    # Step 5: Start nginx in background
    log_info "Starting nginx..."
    nginx -g "daemon on;" &
    NGINX_PID=$!
    log_success "Nginx started with PID $NGINX_PID"
    
    # Step 6: Start FastAPI
    log_info "Starting FastAPI server..."
    exec python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 900 --workers 1
}

# Main execution
main() {
    log_info "🐳 Starting Survey Engine (Docker-optimized)..."
    start_application
}

# Handle signals for graceful shutdown
trap 'log_info "Received shutdown signal, stopping services..."; kill $NGINX_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
