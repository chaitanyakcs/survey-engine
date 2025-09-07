#!/bin/bash

# Test script for Docker setup
set -e

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

# Function to check if Docker is running
check_docker() {
    log_info "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    log_success "Docker is running"
}

# Function to check if .env file exists
check_env() {
    log_info "Checking environment configuration..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env file not found. Copying from .env.example..."
            cp .env.example .env
            log_warning "Please update .env with your actual API keys before running docker-compose up"
        else
            log_error ".env.example file not found. Please create it first."
            exit 1
        fi
    else
        log_success ".env file found"
    fi
}

# Function to validate docker-compose configuration
validate_compose() {
    log_info "Validating docker-compose configuration..."
    if docker-compose config --quiet; then
        log_success "docker-compose configuration is valid"
    else
        log_error "docker-compose configuration is invalid"
        exit 1
    fi
}

# Function to test individual service builds
test_builds() {
    log_info "Testing service builds..."
    
    # Test backend build
    log_info "Building backend service..."
    if docker-compose build backend; then
        log_success "Backend build successful"
    else
        log_error "Backend build failed"
        exit 1
    fi
    
    # Test frontend build
    log_info "Building frontend service..."
    if docker-compose build frontend; then
        log_success "Frontend build successful"
    else
        log_error "Frontend build failed"
        exit 1
    fi
}

# Function to test service startup (quick test)
test_startup() {
    log_info "Testing service startup (quick test)..."
    
    # Start services in background
    log_info "Starting services..."
    docker-compose up -d postgres redis
    
    # Wait for services to be ready
    log_info "Waiting for database and Redis to be ready..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps postgres | grep -q "Up"; then
        log_success "PostgreSQL is running"
    else
        log_error "PostgreSQL failed to start"
        exit 1
    fi
    
    if docker-compose ps redis | grep -q "Up"; then
        log_success "Redis is running"
    else
        log_error "Redis failed to start"
        exit 1
    fi
    
    # Clean up
    log_info "Cleaning up test services..."
    docker-compose down
    log_success "Test services stopped"
}

# Function to show usage instructions
show_usage() {
    echo
    log_info "Docker setup validation complete!"
    echo
    log_info "To start the full application:"
    echo "  docker-compose up -d"
    echo
    log_info "To view logs:"
    echo "  docker-compose logs -f"
    echo
    log_info "To stop the application:"
    echo "  docker-compose down"
    echo
    log_info "Services will be available at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - WebSocket: ws://localhost:8001"
    echo
    log_warning "Make sure to set your REPLICATE_API_TOKEN in .env before starting!"
}

# Main execution
main() {
    log_info "Starting Docker setup validation..."
    
    check_docker
    check_env
    validate_compose
    test_builds
    test_startup
    
    show_usage
    
    log_success "All tests passed! Docker setup is ready."
}

# Run main function
main "$@"
