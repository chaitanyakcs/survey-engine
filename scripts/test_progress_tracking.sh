#!/bin/bash

# Test runner for progress tracking functionality
# Tests both backend and frontend progress coordination

set -e

echo "🧪 Running Progress Tracking Test Suite"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}🔍 $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

print_info "Setting up test environment..."

# Create test results directory
mkdir -p test_results

print_info "Running backend progress tracking tests..."

# Run backend workflow progress tests
python -m pytest tests/test_workflow_progress.py -v \
    --tb=short \
    --junitxml=test_results/backend_progress_results.xml \
    --cov=src.workflows \
    --cov=src.services \
    --cov-report=html:test_results/backend_coverage \
    --cov-report=term-missing

if [ $? -eq 0 ]; then
    print_status "Backend progress tests passed"
else
    print_error "Backend progress tests failed"
    exit 1
fi

print_info "Running integration tests..."

# Run integration tests
python -m pytest tests/test_progress_integration.py -v \
    --tb=short \
    --junitxml=test_results/integration_results.xml \
    --cov-append \
    --cov=src \
    --cov-report=html:test_results/integration_coverage \
    --cov-report=term-missing

if [ $? -eq 0 ]; then
    print_status "Integration tests passed"
else
    print_error "Integration tests failed"
    exit 1
fi

print_info "Running frontend progress tests..."

# Change to frontend directory and run tests
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

# Run frontend tests
npm test -- --testPathPattern=ProgressStepper.test.tsx \
    --coverage \
    --coverageDirectory=../test_results/frontend_coverage \
    --watchAll=false \
    --passWithNoTests

if [ $? -eq 0 ]; then
    print_status "Frontend progress tests passed"
else
    print_error "Frontend progress tests failed"
    exit 1
fi

cd ..

print_info "Running progress mapping validation..."

# Run a quick validation of step mappings
python -c "
import sys
sys.path.append('.')

# Backend steps validation
from tests.test_progress_integration import TestProgressRegressionSafeguards
test_instance = TestProgressRegressionSafeguards()

try:
    test_instance.test_frontend_step_mapping_completeness()
    test_instance.test_progress_percentage_ranges_are_valid()
    print('✅ Progress mapping validation passed')
except AssertionError as e:
    print(f'❌ Progress mapping validation failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Validation error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Progress mapping validation passed"
else
    print_error "Progress mapping validation failed"
    exit 1
fi

echo ""
echo "🎉 All Progress Tracking Tests Passed!"
echo "======================================"
print_status "Backend workflow progress tests: PASSED"
print_status "Integration tests: PASSED"
print_status "Frontend progress tests: PASSED"
print_status "Progress mapping validation: PASSED"

echo ""
print_info "Test Results Summary:"
echo "📊 Backend coverage report: test_results/backend_coverage/index.html"
echo "📊 Integration coverage report: test_results/integration_coverage/index.html"
echo "📊 Frontend coverage report: test_results/frontend_coverage/index.html"
echo "📋 Backend test results: test_results/backend_progress_results.xml"
echo "📋 Integration test results: test_results/integration_results.xml"

echo ""
print_status "Progress tracking implementation is working correctly!"
echo "🚀 Ready for production deployment"


