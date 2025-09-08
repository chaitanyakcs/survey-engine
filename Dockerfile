# Multi-stage build for full-stack application
FROM node:18-alpine as frontend-build

# Build React frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

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
RUN pip install --no-cache-dir torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Pre-download ML models to avoid startup delays
RUN python3 -c "from sentence_transformers import SentenceTransformer; print('Pre-downloading sentence-transformers model...'); model = SentenceTransformer('all-MiniLM-L6-v2'); print('Model downloaded successfully!'); print('Testing model encoding...'); embedding = model.encode('test text for model validation'); print(f'Model encoding test successful, embedding dimension: {len(embedding)}'); print('All model variants downloaded and tested successfully!')"

# Copy all application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY websocket_server.py ./
COPY start.sh ./
COPY start-local.sh ./
COPY preload_models.py ./
COPY seed_rules.py ./
COPY migrations/ ./migrations/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build /app/frontend/build

# Create nginx configuration
RUN printf 'user app;\nworker_processes auto;\npid /app/nginx.pid;\n\nevents {\n    worker_connections 1024;\n}\n\nhttp {\n    include /etc/nginx/mime.types;\n    default_type application/octet-stream;\n    \n    sendfile on;\n    keepalive_timeout 65;\n    \n    # Global timeout settings for ML model loading\n    proxy_connect_timeout       600s;\n    proxy_send_timeout          600s;\n    proxy_read_timeout          600s;\n    send_timeout               600s;\n    \n    server {\n        listen 80;\n        server_name _;\n        root /app/frontend/build;\n        index index.html;\n\n        # Serve React app\n        location / {\n            try_files $uri $uri/ /index.html;\n        }\n\n        # API health check - direct proxy to FastAPI\n        location = /api/health {\n            proxy_pass http://127.0.0.1:8000/health;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n\n        # API proxy to FastAPI backend\n        location /api/ {\n            proxy_pass http://127.0.0.1:8000;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n            proxy_set_header Connection "";\n            proxy_http_version 1.1;\n            proxy_buffering off;\n            proxy_cache off;\n            # Increase timeouts for ML model loading\n            proxy_connect_timeout       600s;\n            proxy_send_timeout          600s;\n            proxy_read_timeout          600s;\n        }\n\n        # WebSocket proxy to FastAPI server (consolidated)\n        location /ws/ {\n            proxy_pass http://127.0.0.1:8000/ws/;\n            proxy_http_version 1.1;\n            proxy_set_header Upgrade $http_upgrade;\n            proxy_set_header Connection "upgrade";\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n\n        # Health check endpoint - proxy to FastAPI (exact match)\n        location = /health {\n            proxy_pass http://127.0.0.1:8000/health;\n            proxy_set_header Host $host;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n    }\n}\n' > /etc/nginx/nginx.conf

# Make startup scripts executable
RUN chmod +x /app/start.sh && \
    chmod +x /app/start-local.sh && \
    chmod +x /app/websocket_server.py && \
    chmod +x /app/seed_rules.py

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
CMD ["/app/start.sh"]# Force Railway rebuild
# Force Railway rebuild - Tue Sep  9 00:57:59 IST 2025
