#!/usr/bin/env python3
"""
Test Runner Script

Provides easy commands to run different types of tests locally
and verify quality before committing code.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class TestRunner:
    """Main test runner class"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.success_count = 0
        self.failure_count = 0

    def run_command(self, command, description, cwd=None, env=None):
        """Run a command and track success/failure"""
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{description}{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"Running: {command}")
        print()

        # Merge environment variables
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                env=full_env,
                check=True
            )
            duration = time.time() - start_time
            print(f"\n{Colors.GREEN}✅ {description} - PASSED ({duration:.1f}s){Colors.END}")
            self.success_count += 1
            return True

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"\n{Colors.RED}❌ {description} - FAILED ({duration:.1f}s){Colors.END}")
            print(f"Exit code: {e.returncode}")
            self.failure_count += 1
            return False

    def setup_test_environment(self):
        """Set up test environment variables"""
        return {
            'DATABASE_URL': 'postgresql://chaitanya@localhost:5432/survey_engine_test',
            'REDIS_URL': 'redis://localhost:6379',
            'REPLICATE_API_TOKEN': 'test_token',
            'OPENAI_API_KEY': 'test_key',
            'DEBUG': 'true',
            'LOG_LEVEL': 'WARNING',  # Reduce noise during testing
            'PYTHONPATH': str(self.project_root)
        }

    def run_backend_tests(self, coverage=True, specific_test=None):
        """Run backend Python tests"""
        test_env = self.setup_test_environment()

        # Base pytest command
        cmd_parts = ['python', '-m', 'pytest']

        if specific_test:
            cmd_parts.append(specific_test)
        else:
            cmd_parts.append('tests/')

        # Add coverage if requested
        if coverage:
            cmd_parts.extend([
                '--cov=src',
                '--cov-report=term-missing',
                '--cov-report=html',
                '--cov-fail-under=75'
            ])

        # Add verbose output
        cmd_parts.extend(['-v', '--tb=short'])

        command = ' '.join(cmd_parts)
        return self.run_command(
            command,
            "Backend Tests" + (f" ({specific_test})" if specific_test else ""),
            env=test_env
        )

    def run_core_service_tests(self):
        """Run tests for core services specifically"""
        test_env = self.setup_test_environment()

        core_tests = [
            'tests/test_generation_service.py',
            'tests/test_prompt_service.py',
            'tests/test_document_parser.py'
        ]

        success = True
        for test_file in core_tests:
            if not self.run_command(
                f'python -m pytest {test_file} -v',
                f"Core Service Test: {test_file.split('/')[-1]}",
                env=test_env
            ):
                success = False

        return success

    def run_frontend_tests(self):
        """Run frontend tests"""
        frontend_dir = self.project_root / 'frontend'

        if not frontend_dir.exists():
            print(f"{Colors.YELLOW}⚠️ Frontend directory not found, skipping frontend tests{Colors.END}")
            return True

        # Install dependencies if needed
        if not (frontend_dir / 'node_modules').exists():
            if not self.run_command(
                'npm install',
                "Installing Frontend Dependencies",
                cwd=frontend_dir
            ):
                return False

        # Run tests
        return self.run_command(
            'npm test -- --coverage --watchAll=false',
            "Frontend Tests",
            cwd=frontend_dir
        )

    def run_quality_regression_check(self):
        """Run quality regression detection"""
        test_env = self.setup_test_environment()

        # Create a simple quality check script
        quality_check_script = '''
import asyncio
import sys
from src.services.quality_regression_service import QualityRegressionService

async def main():
    try:
        service = QualityRegressionService()

        print("🔍 Running quality regression detection...")
        alerts = await service.detect_regressions(lookback_hours=24)

        print(f"📊 Detected {len(alerts)} quality regressions")

        # Check for severe regressions
        severe_alerts = [a for a in alerts if a.regression_severity == 'severe']
        if severe_alerts:
            print(f"🚨 {len(severe_alerts)} SEVERE regressions detected!")
            for alert in severe_alerts:
                print(f"  - {alert.metric_name}: {alert.description}")
            return 1

        print("✅ No severe quality regressions detected")
        return 0

    except Exception as e:
        print(f"❌ Quality check failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
'''

        # Write temporary script
        script_path = self.project_root / 'temp_quality_check.py'
        with open(script_path, 'w') as f:
            f.write(quality_check_script)

        try:
            success = self.run_command(
                f'python {script_path}',
                "Quality Regression Check",
                env=test_env
            )
        finally:
            # Clean up temporary script
            if script_path.exists():
                script_path.unlink()

        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"{Colors.HEADER}🚀 Running Complete Test Suite{Colors.END}")
        print()

        tests = [
            ("Backend Tests", self.run_backend_tests),
            ("Core Service Tests", self.run_core_service_tests),
            ("Frontend Tests", self.run_frontend_tests),
            ("Quality Regression Check", self.run_quality_regression_check)
        ]

        for test_name, test_func in tests:
            print(f"\n{Colors.BLUE}📋 Starting: {test_name}{Colors.END}")
            test_func()

    def print_summary(self):
        """Print test summary"""
        total_tests = self.success_count + self.failure_count

        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")

        if self.failure_count == 0:
            print(f"{Colors.GREEN}🎉 All tests passed! ({self.success_count}/{total_tests}){Colors.END}")
            exit_code = 0
        else:
            print(f"{Colors.RED}❌ Some tests failed ({self.failure_count}/{total_tests}){Colors.END}")
            print(f"{Colors.GREEN}✅ Passed: {self.success_count}{Colors.END}")
            print(f"{Colors.RED}❌ Failed: {self.failure_count}{Colors.END}")
            exit_code = 1

        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        return exit_code


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Survey Engine Test Runner')
    parser.add_argument(
        'test_type',
        nargs='?',
        choices=['all', 'backend', 'frontend', 'core', 'quality'],
        default='all',
        help='Type of tests to run'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Skip coverage reporting for faster execution'
    )
    parser.add_argument(
        '--test',
        help='Run specific test file or test function'
    )

    args = parser.parse_args()

    runner = TestRunner()

    try:
        if args.test_type == 'all':
            runner.run_all_tests()
        elif args.test_type == 'backend':
            runner.run_backend_tests(coverage=not args.no_coverage, specific_test=args.test)
        elif args.test_type == 'frontend':
            runner.run_frontend_tests()
        elif args.test_type == 'core':
            runner.run_core_service_tests()
        elif args.test_type == 'quality':
            runner.run_quality_regression_check()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Tests interrupted by user{Colors.END}")
        runner.failure_count += 1

    exit_code = runner.print_summary()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()