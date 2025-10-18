#!/bin/bash

# Survey Engine Docker Startup Script
# Handles Docker Compose services with frontend development support

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
FRONTEND_DIR="frontend"

echo -e "${BLUE}🐳 Starting Survey Engine with Docker...${NC}"

# Function to check if Docker is running
check_docker() {
    echo -e "${YELLOW}🔍 Checking Docker availability...${NC}"
    
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo -e "${YELLOW}Please install Docker from: https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        echo -e "${YELLOW}Please start Docker Desktop or the Docker daemon${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker is available and running${NC}"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    echo -e "${YELLOW}🔍 Checking Docker Compose availability...${NC}"
    
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
        echo -e "${GREEN}✅ Using docker-compose${NC}"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✅ Using docker compose (plugin)${NC}"
    else
        echo -e "${RED}❌ Docker Compose is not available${NC}"
        exit 1
    fi
}

# Function to build frontend
build_frontend() {
    echo -e "${YELLOW}🏗️  Building frontend...${NC}"
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
        exit 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists, if not install dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Build the frontend
    echo -e "${BLUE}🔨 Building React application...${NC}"
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend build completed successfully${NC}"
    else
        echo -e "${RED}❌ Frontend build failed${NC}"
        exit 1
    fi
    
    cd ..
}

# Function to start Docker services
start_services() {
    echo -e "${YELLOW}🚀 Starting Docker services...${NC}"
    
    # Stop any existing containers
    echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
    $COMPOSE_CMD down --remove-orphans
    
    # Build and start services (force rebuild for local architecture)
    echo -e "${BLUE}🏗️  Building and starting services for $(uname -m) architecture...${NC}"
    $COMPOSE_CMD build --no-cache
    $COMPOSE_CMD up -d
    
    echo -e "${GREEN}✅ Docker services started${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}📊 Running database migrations...${NC}"
    
    # Wait for database to be ready
    echo -e "${BLUE}⏳ Waiting for database to be ready...${NC}"
    sleep 10
    
    # Run migrations using the admin API system
    if $COMPOSE_CMD exec backend python3 run_migrations.py; then
        echo -e "${GREEN}✅ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠️  Migration failed, trying alternative approach...${NC}"
        # Try using docker run if exec fails
        if $COMPOSE_CMD run --rm backend python3 run_migrations.py; then
            echo -e "${GREEN}✅ Database migrations completed (alternative method)${NC}"
        else
            echo -e "${RED}❌ Database migrations failed${NC}"
            echo -e "${YELLOW}You may need to run migrations manually:${NC}"
            echo -e "${CYAN}  $COMPOSE_CMD exec backend python3 run_migrations.py${NC}"
        fi
    fi
}

# Function to seed database
seed_database() {
    echo -e "${YELLOW}🌱 Seeding database...${NC}"
    
    echo -e "${GREEN}✅ Rules are managed via database migrations${NC}"
    echo -e "${BLUE}💡 No separate seeding needed - migrations handle rule creation${NC}"
}

# Function to show service status and URLs
show_status() {
    echo -e "${PURPLE}📊 Service Status:${NC}"
    echo ""
    
    # Check service health
    services=("backend" "websocket" "frontend" "postgres" "redis")
    for service in "${services[@]}"; do
        if $COMPOSE_CMD ps | grep -q "${service}.*Up"; then
            echo -e "${GREEN}✅ $service: Running${NC}"
        else
            echo -e "${RED}❌ $service: Not running${NC}"
        fi
    done
    
    echo ""
    echo -e "${CYAN}🌐 Access URLs:${NC}"
    echo -e "${GREEN}  Frontend:        http://localhost:3000${NC}"
    echo -e "${GREEN}  Backend API:     http://localhost:8000${NC}"
    echo -e "${GREEN}  API Docs:        http://localhost:8000/docs${NC}"
    echo -e "${GREEN}  ReDoc:           http://localhost:8000/redoc${NC}"
    echo ""
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}📋 Following logs (Ctrl+C to stop)...${NC}"
    echo -e "${CYAN}To follow specific service logs: $COMPOSE_CMD logs -f <service-name>${NC}"
    echo -e "${CYAN}Available services: backend, websocket, frontend, postgres, redis${NC}"
    echo ""
    
    $COMPOSE_CMD logs -f
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping Docker services...${NC}"
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Function to cleanup (stop and remove everything)
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    $COMPOSE_CMD down --volumes --remove-orphans --rmi local
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to restart a specific service
restart_service() {
    local service=$1
    if [ -z "$service" ]; then
        echo -e "${RED}❌ Service name required${NC}"
        echo -e "${YELLOW}Available services: backend, websocket, frontend, postgres, redis${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🔄 Restarting $service...${NC}"
    $COMPOSE_CMD restart "$service"
    echo -e "${GREEN}✅ $service restarted${NC}"
}

# Function to rebuild and restart frontend
rebuild_frontend() {
    echo -e "${YELLOW}🔄 Rebuilding frontend...${NC}"
    
    # Build frontend
    build_frontend
    
    # Restart frontend container
    echo -e "${BLUE}🔄 Restarting frontend container...${NC}"
    $COMPOSE_CMD up --build -d frontend
    
    echo -e "${GREEN}✅ Frontend rebuilt and restarted${NC}"
    echo -e "${CYAN}Frontend available at: http://localhost:3000${NC}"
}

# Function to enter a container shell
shell() {
    local service=${1:-backend}
    echo -e "${YELLOW}🐚 Opening shell in $service container...${NC}"
    $COMPOSE_CMD exec "$service" /bin/bash
}

# Main execution function
main() {
    echo -e "${BLUE}🎯 Docker Startup Sequence${NC}"
    echo -e "${BLUE}===========================${NC}"
    
    # Step 1: Check Docker
    check_docker
    check_docker_compose
    
    # Step 2: Build frontend
    build_frontend
    
    # Step 3: Start services
    start_services
    
    # Step 4: Wait a bit for services to initialize
    echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
    sleep 15
    
    # Step 5: Run migrations and seeding
    run_migrations
    seed_database
    
    # Step 6: Show status
    show_status
    
    echo -e "${GREEN}🎉 Survey Engine is ready!${NC}"
    echo -e "${CYAN}Run '$0 logs' to follow application logs${NC}"
    echo -e "${CYAN}Run '$0 stop' to stop all services${NC}"
}

# Handle command line arguments
case "${1:-start}" in
    "start"|"")
        main
        ;;
    "stop")
        check_docker
        check_docker_compose
        stop_services
        ;;
    "restart")
        check_docker
        check_docker_compose
        stop_services
        main
        ;;
    "logs")
        check_docker
        check_docker_compose
        show_logs
        ;;
    "status")
        check_docker
        check_docker_compose
        show_status
        ;;
    "cleanup")
        check_docker
        check_docker_compose
        cleanup
        ;;
    "rebuild-frontend")
        check_docker
        check_docker_compose
        rebuild_frontend
        ;;
    "build-local")
        check_docker
        check_docker_compose
        echo -e "${YELLOW}🏗️  Building images for local $(uname -m) architecture...${NC}"
        build_frontend
        $COMPOSE_CMD build --no-cache
        echo -e "${GREEN}✅ Local build completed${NC}"
        ;;
    "restart-service")
        check_docker
        check_docker_compose
        restart_service "$2"
        ;;
    "shell")
        check_docker
        check_docker_compose
        shell "$2"
        ;;
    "migrate")
        check_docker
        check_docker_compose
        run_migrations
        ;;
    "seed")
        check_docker
        check_docker_compose
        seed_database
        ;;
    "help")
        echo "Survey Engine Docker Startup Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start            - Full startup sequence (default)"
        echo "  stop             - Stop all services"
        echo "  restart          - Stop and restart all services"
        echo "  logs             - Follow application logs"
        echo "  status           - Show service status and URLs"
        echo "  cleanup          - Stop services and remove all Docker resources"
        echo "  rebuild-frontend - Rebuild and restart just the frontend"
        echo "  build-local      - Build images for local ARM64/AMD64 architecture"
        echo "  restart-service  - Restart a specific service (backend, frontend, etc.)"
        echo "  shell            - Open shell in container (default: backend)"
        echo "  migrate          - Run database migrations only"
        echo "  seed             - Seed database only"
        echo "  help             - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                           # Start everything"
        echo "  $0 restart-service frontend  # Restart just frontend"
        echo "  $0 shell backend             # Open shell in backend container"
        echo "  $0 logs                      # Follow logs"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac