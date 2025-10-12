#!/bin/bash
#
# Unified Test Runner for Survey Engine
# Usage: ./scripts/run_tests.sh [command] [options]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
STRICT=false
VERBOSE=false
QUIET=false

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --quiet|-q)
            QUIET=true
            shift
            ;;
        *)
            COMMAND=$1
            shift
            ;;
    esac
done

# Default to 'all' if no command specified
COMMAND=${COMMAND:-all}

# Function to run tests with optional coverage
run_tests() {
    local test_path=$1
    local test_name=$2
    local marker=$3
    
    if [ "$QUIET" = false ]; then
        echo -e "${BLUE}🧪 Running $test_name...${NC}"
    fi
    
    # Build pytest command
    local cmd="uv run pytest $test_path"
    
    # Add marker if specified
    if [ ! -z "$marker" ]; then
        cmd="$cmd -m $marker"
    fi
    
    # Add coverage if enabled
    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=src --cov-report=html --cov-report=term-missing"
    fi
    
    # Add verbose if enabled
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd -v"
    elif [ "$QUIET" = true ]; then
        cmd="$cmd -q"
    else
        cmd="$cmd --tb=short"
    fi
    
    # Add strict mode if enabled (stop on first failure)
    if [ "$STRICT" = true ]; then
        cmd="$cmd -x"
    fi
    
    # Run the tests
    local temp_output=$(mktemp)
    if eval $cmd > "$temp_output" 2>&1; then
        if [ "$QUIET" = false ]; then
            echo -e "${GREEN}✅ $test_name PASSED${NC}"
        fi
        rm -f "$temp_output"
        return 0
    else
        if [ "$QUIET" = false ]; then
            echo -e "${RED}❌ $test_name FAILED${NC}"
        fi
        # Show last 20 lines of output on failure
        echo -e "${YELLOW}Last 20 lines of test output:${NC}"
        tail -20 "$temp_output" 2>/dev/null || echo "No output captured"
        rm -f "$temp_output"
        return 1
    fi
}

# Main test commands
case $COMMAND in
    critical)
        echo -e "${YELLOW}🎯 Running CRITICAL tests only (must pass for deployment)${NC}"
        echo -e "${YELLOW}Expected duration: <2 minutes${NC}"
        echo ""
        run_tests "tests/unit/" "Critical Tests" "critical"
        ;;
    
    smoke)
        echo -e "${YELLOW}💨 Running SMOKE tests (ultra-fast)${NC}"
        echo -e "${YELLOW}Expected duration: <30 seconds${NC}"
        echo ""
        run_tests "tests/unit/" "Smoke Tests" "smoke"
        ;;
    
    unit)
        echo -e "${YELLOW}🔬 Running UNIT tests${NC}"
        echo ""
        run_tests "tests/unit/" "Unit Tests" ""
        ;;
    
    integration)
        echo -e "${YELLOW}🔗 Running INTEGRATION tests${NC}"
        echo -e "${YELLOW}Expected duration: 2-5 minutes${NC}"
        echo ""
        run_tests "tests/integration/" "Integration Tests" ""
        ;;
    
    api)
        echo -e "${YELLOW}🌐 Running API tests${NC}"
        echo ""
        run_tests "tests/api/" "API Tests" ""
        ;;
    
    evaluation)
        echo -e "${YELLOW}📊 Running EVALUATION tests${NC}"
        echo ""
        run_tests "tests/evaluation/" "Evaluation Tests" ""
        ;;
    
    progress)
        echo -e "${YELLOW}📈 Running PROGRESS TRACKING tests${NC}"
        echo ""
        run_tests "tests/integration/test_workflow_progress.py tests/integration/test_progress_integration.py" "Progress Tests" ""
        ;;
    
    slow)
        echo -e "${YELLOW}🐌 Running SLOW tests (nightly/weekly)${NC}"
        echo -e "${YELLOW}Expected duration: >5 minutes${NC}"
        echo ""
        run_tests "tests/" "Slow Tests" "slow"
        ;;
    
    all)
        echo -e "${YELLOW}🚀 Running ALL tests (except slow)${NC}"
        echo ""
        
        # Run tests in order of importance
        FAILED=0
        
        run_tests "tests/unit/" "Unit Tests" "" || FAILED=1
        run_tests "tests/integration/" "Integration Tests" "" || FAILED=1
        run_tests "tests/api/" "API Tests" "" || FAILED=1
        
        if [ $FAILED -eq 0 ]; then
            echo -e "${GREEN}🎉 All tests PASSED!${NC}"
        else
            echo -e "${RED}❌ Some tests FAILED${NC}"
            exit 1
        fi
        ;;
    
    deploy)
        echo -e "${YELLOW}🚢 Running DEPLOYMENT test suite${NC}"
        echo -e "${YELLOW}This runs only critical tests that must pass before deployment${NC}"
        echo ""
        
        # Run critical tests with strict mode
        STRICT=true
        run_tests "tests/unit/" "Critical Tests" "critical"
        
        echo ""
        echo -e "${GREEN}✅ Deployment tests PASSED - safe to deploy!${NC}"
        ;;
    
    help|--help|-h)
        echo "Survey Engine Test Runner"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  critical     - Run critical tests only (must pass for deployment, <2min)"
        echo "  smoke        - Run ultra-fast smoke tests (<30s)"
        echo "  unit         - Run all unit tests"
        echo "  integration  - Run integration tests (2-5min)"
        echo "  api          - Run API endpoint tests"
        echo "  evaluation   - Run evaluation system tests"
        echo "  progress     - Run progress tracking tests"
        echo "  slow         - Run slow tests (>5min, for nightly/weekly runs)"
        echo "  all          - Run all tests except slow (default)"
        echo "  deploy       - Run deployment test suite (critical tests only)"
        echo "  help         - Show this help message"
        echo ""
        echo "Options:"
        echo "  --coverage   - Generate coverage report"
        echo "  --strict     - Stop on first failure"
        echo "  --verbose,-v - Verbose output"
        echo "  --quiet,-q   - Quiet output (minimal logging)"
        echo ""
        echo "Examples:"
        echo "  $0 critical                    # Quick critical tests"
        echo "  $0 unit --coverage             # Unit tests with coverage"
        echo "  $0 all --verbose --strict      # All tests, verbose, stop on failure"
        echo "  $0 deploy                      # Pre-deployment test suite"
        echo ""
        ;;
    
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac

