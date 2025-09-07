FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy all application code (including websocket_server.py)
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY websocket_server.py ./
COPY start.sh ./

# Make startup script executable and fix permissions
RUN chmod +x /app/start.sh && \
    chmod +x /app/websocket_server.py

# Install pg_isready and redis-cli for health checks
RUN apt-get update && apt-get install -y postgresql-client redis-tools && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy uv to a location accessible by app user
RUN cp /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

RUN chown -R app:app /app

USER app

# Expose port (will be overridden by Railway)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the application
CMD ["/app/start.sh"]