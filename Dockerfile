# Multi-stage build for full-stack application
# Note: Using pre-built frontend from local build

# Python backend stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install system dependencies including nginx
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency files
COPY requirements-docker.txt ./

# Install PyTorch CPU version first
RUN pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Pre-download ML models to avoid startup delays
RUN python3 -c "from sentence_transformers import SentenceTransformer; print('Pre-downloading sentence-transformers model...'); model = SentenceTransformer('all-MiniLM-L6-v2'); print('Model downloaded successfully!'); print('Testing model encoding...'); embedding = model.encode('test text for model validation'); print(f'Model encoding test successful, embedding dimension: {len(embedding)}'); print('All model variants downloaded and tested successfully!')"

# Copy all application code
COPY src/ ./src/
COPY evaluations/ ./evaluations/
COPY start.sh ./
COPY start-local.sh ./
COPY preload_models.py ./
# Rules are seeded via migrations, no separate seeding needed
COPY run_migrations.py ./
COPY migrations/ ./migrations/

# Copy pre-built frontend from local build
COPY frontend/build /app/frontend/build

# Create nginx configuration
RUN cat > /etc/nginx/nginx.conf << 'EOF'
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
        listen 80;
        server_name _;
        root /app/frontend/build;
        index index.html;

        # Serve React app
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API health check - direct proxy to FastAPI
        location = /api/health {
            proxy_pass http://127.0.0.1:8000/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API proxy to FastAPI backend
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_cache off;
            # Increase timeouts for ML model loading
            proxy_connect_timeout       600s;
            proxy_send_timeout          600s;
            proxy_read_timeout          600s;
        }

        # WebSocket proxy to FastAPI server (consolidated)
        location /ws/ {
            proxy_pass http://127.0.0.1:8000/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint - proxy to FastAPI (exact match)
        location = /health {
            proxy_pass http://127.0.0.1:8000/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Make startup scripts executable
RUN chmod +x /app/start.sh && \
    chmod +x /app/start-local.sh

# Rules are seeded via migrations, no separate seeding needed

# Install pg_isready and redis-cli for health checks
RUN apt-get update && apt-get install -y postgresql-client redis-tools && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy uv to a location accessible by app user
RUN cp /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

# Make nginx runnable by app user and set up directories
RUN chmod +x /usr/sbin/nginx && \
    mkdir -p /var/log/nginx /var/lib/nginx /var/cache/nginx && \
    chown -R app:app /var/log/nginx /var/lib/nginx /var/cache/nginx /etc/nginx

RUN chown -R app:app /app

USER app

# Expose port (Railway will assign PORT environment variable)
EXPOSE ${PORT:-80}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-80}/health || exit 1

# Start the application
CMD ["/app/start.sh"]