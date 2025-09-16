#!/usr/bin/env python3
"""
Standardized test runner for survey-engine project
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for survey-engine project")
    parser.add_argument("--type", choices=["unit", "integration", "api", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    parser.add_argument("--markers", help="Pytest markers to filter tests")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd_parts = ["python3", "-m", "pytest"]
    
    # Add test paths based on type
    if args.type == "unit":
        cmd_parts.extend(["tests/unit/", "-m", "unit"])
    elif args.type == "integration":
        cmd_parts.extend(["tests/integration/", "-m", "integration"])
    elif args.type == "api":
        cmd_parts.extend(["tests/api/", "-m", "api"])
    else:  # all
        cmd_parts.extend(["tests/"])
    
    # Add coverage if requested
    if args.coverage:
        cmd_parts.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add verbose output
    if args.verbose:
        cmd_parts.append("-vv")
    
    # Add parallel execution
    if args.parallel:
        cmd_parts.extend(["-n", str(args.parallel)])
    
    # Add markers filter
    if args.markers:
        cmd_parts.extend(["-m", args.markers])
    
    # Add additional options
    cmd_parts.extend([
        "--tb=short",
        "--disable-warnings",
        "--color=yes",
        "--durations=10"
    ])
    
    cmd = " ".join(cmd_parts)
    
    print("🚀 Survey Engine Test Runner")
    print(f"📋 Running {args.type} tests")
    if args.coverage:
        print("📊 With coverage reporting")
    if args.parallel:
        print(f"⚡ With {args.parallel} parallel workers")
    
    success = run_command(cmd, f"Running {args.type} tests")
    
    if success:
        print(f"\n✅ All {args.type} tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Some {args.type} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

