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
SEED_SCRIPT="seed_rules.py"
APP_PORT=${PORT:-8080}
FASTAPI_PORT=${FASTAPI_PORT:-8000}

echo -e "${BLUE}🚀 Starting Survey Engine...${NC}"

# Function to check if database is ready
check_database() {
    echo -e "${YELLOW}🔍 Checking database connection...${NC}"
    
    # Set default DATABASE_URL if not provided
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️  No DATABASE_URL found, using default local development settings${NC}"
        export DATABASE_URL="postgresql://survey_engine:development_password@127.0.0.1:5433/survey_engine_db"
        export REDIS_URL="redis://127.0.0.1:6379"
    fi
    
    # Try to connect to database
    echo -e "${BLUE}🔍 Testing connection to: $DATABASE_URL${NC}"
    if DATABASE_URL="$DATABASE_URL" python3 -c "
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

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}📊 Running database migrations...${NC}"
    
    # Check if migrations directory exists
    if [ ! -d "$DB_MIGRATIONS_DIR" ]; then
        echo -e "${YELLOW}⚠️  No migrations directory found, skipping migrations${NC}"
        return
    fi
    
    # Run migrations in order
    for migration in $(ls $DB_MIGRATIONS_DIR/*.sql | sort); do
        echo -e "${BLUE}📝 Running migration: $(basename $migration)${NC}"
        
        if PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\([^@]*\)@.*/\1/p') psql "$DATABASE_URL" -f "$migration"; then
            echo -e "${GREEN}✅ Migration $(basename $migration) completed${NC}"
        else
            echo -e "${RED}❌ Migration $(basename $migration) failed${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ All migrations completed${NC}"
}

# Function to seed the database
seed_database() {
    echo -e "${YELLOW}🌱 Seeding database with rules...${NC}"
    
    if [ -f "$SEED_SCRIPT" ]; then
        if DATABASE_URL="$DATABASE_URL" python3 "$SEED_SCRIPT"; then
            echo -e "${GREEN}✅ Database seeding completed${NC}"
        else
            echo -e "${RED}❌ Database seeding failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Seed script not found, skipping seeding${NC}"
    fi
}

# Function to start the application
start_application() {
    echo -e "${YELLOW}🚀 Starting application...${NC}"
    
    # Check if we're in Railway (has PORT env var) or local development
    if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$PORT" ]; then
        echo -e "${BLUE}🏗️  Starting in production mode (Railway)${NC}"
        echo -e "${BLUE}   - Nginx will run on port $APP_PORT${NC}"
        echo -e "${BLUE}   - FastAPI will run on port $FASTAPI_PORT${NC}"
        
        # Start the consolidated application
        DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" ./start.sh consolidated
    else
        echo -e "${BLUE}🏠 Starting in development mode${NC}"
        
        # For local development, start both nginx and FastAPI
        echo -e "${BLUE}   - Nginx will run on port 4321${NC}"
        echo -e "${BLUE}   - FastAPI will run on port $FASTAPI_PORT${NC}"
        echo -e "${BLUE}   - Frontend will be served by nginx from build directory${NC}"
        
        # Check if frontend is built
        if [ ! -d "frontend/build" ]; then
            echo -e "${YELLOW}⚠️  Frontend not built, building now...${NC}"
            cd frontend && npm run build && cd ..
        fi
        
        # Start FastAPI in background
        echo -e "${YELLOW}🔄 Starting FastAPI server...${NC}"
        DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" python3 -m uvicorn src.main:app --host 0.0.0.0 --port $FASTAPI_PORT --reload &
        FASTAPI_PID=$!
        
        # Wait for FastAPI to be ready
        echo -e "${YELLOW}⏳ Waiting for FastAPI to be ready...${NC}"
        sleep 5
        
        # Start nginx
        echo -e "${YELLOW}🔄 Starting nginx...${NC}"
        /opt/homebrew/opt/nginx/bin/nginx -c "$(pwd)/nginx-local.conf" -g "daemon off;" &
        NGINX_PID=$!
        
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        echo -e "${GREEN}   - Frontend: http://localhost:4321${NC}"
        echo -e "${GREEN}   - API: http://localhost:4321/api${NC}"
        echo -e "${GREEN}   - WebSocket: ws://localhost:4321/ws${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        
        # Function to handle shutdown
        cleanup() {
            echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
            if [ ! -z "$NGINX_PID" ]; then
                kill $NGINX_PID 2>/dev/null || true
                echo -e "${GREEN}✅ Nginx stopped${NC}"
            fi
            if [ ! -z "$FASTAPI_PID" ]; then
                kill $FASTAPI_PID 2>/dev/null || true
                echo -e "${GREEN}✅ FastAPI stopped${NC}"
            fi
            exit 0
        }
        
        # Set up signal handlers
        trap cleanup SIGTERM SIGINT
        
        # Wait for any process to exit
        wait $NGINX_PID $FASTAPI_PID
    fi
}

# Function to preload models
preload_models() {
    echo -e "${YELLOW}🧠 Preloading ML models...${NC}"
    
    if python3 -c "
import sys
sys.path.append('src')
from src.services.embedding_service import EmbeddingService
import asyncio

async def preload():
    try:
        service = EmbeddingService()
        await service.preload_models()
        print('Models preloaded successfully')
    except Exception as e:
        print(f'Model preloading failed: {e}')
        # Don't exit on model preload failure
        pass

asyncio.run(preload())
"; then
        echo -e "${GREEN}✅ Models preloaded successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Model preloading failed, continuing without preloaded models${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🎯 Survey Engine Startup Sequence${NC}"
    echo -e "${BLUE}================================${NC}"
    
    # Step 1: Check database connection
    check_database
    
    # Step 2: Run migrations
    run_migrations
    
    # Step 3: Seed database
    seed_database
    
    # Step 4: Preload models (in background)
    preload_models &
    
    # Step 5: Start application
    start_application
}

# Handle command line arguments
case "${1:-startup}" in
    "startup")
        main
        ;;
    "migrate")
        check_database
        run_migrations
        ;;
    "seed")
        check_database
        seed_database
        ;;
    "preload")
        preload_models
        ;;
    "help")
        echo "Survey Engine Startup Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  startup  - Full startup sequence (default)"
        echo "  migrate  - Run database migrations only"
        echo "  seed     - Seed database only"
        echo "  preload  - Preload ML models only"
        echo "  help     - Show this help message"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
