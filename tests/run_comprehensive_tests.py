#!/usr/bin/env python3
"""
Comprehensive test runner for the survey engine
Runs all critical tests focusing on system prompt generation and output parsing
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_test_file(test_file: str, verbose: bool = True) -> tuple[bool, str]:
    """Run a single test file and return success status and output"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file} PASSED ({duration:.2f}s)")
            if verbose:
                print(result.stdout)
            return True, result.stdout
        else:
            print(f"❌ {test_file} FAILED ({duration:.2f}s)")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, result.stderr
            
    except Exception as e:
        print(f"💥 {test_file} ERROR: {str(e)}")
        return False, str(e)

def run_all_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Test Suite")
    print("=" * 60)
    
    # Define test files in order of importance
    test_files = [
        "test_prompt_builder_simple.py",
        "test_question_type_components.py",
        "test_prompt_service.py",
        "test_survey_parsing.py",
        "test_generation_service.py",
        "test_validation_service.py"
    ]
    
    # Check which test files exist
    existing_tests = []
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            existing_tests.append(test_file)
        else:
            print(f"⚠️  {test_file} not found, skipping")
    
    if not existing_tests:
        print("❌ No test files found!")
        return False
    
    print(f"📋 Found {len(existing_tests)} test files to run")
    
    # Run tests
    results = []
    total_start_time = time.time()
    
    for test_file in existing_tests:
        success, output = run_test_file(test_file, verbose=False)
        results.append((test_file, success, output))
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Duration: {total_duration:.2f}s")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for test_file, success, output in results:
            if not success:
                print(f"  - {test_file}")
    
    print(f"\n{'='*60}")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"💥 {failed} TESTS FAILED!")
        return False

def run_specific_tests():
    """Run specific critical tests"""
    print("🎯 Running Critical Tests Only")
    print("=" * 60)
    
    critical_tests = [
        "test_prompt_builder_simple.py",
        "test_question_type_components.py"
    ]
    
    results = []
    for test_file in critical_tests:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            success, output = run_test_file(test_file, verbose=True)
            results.append((test_file, success, output))
        else:
            print(f"⚠️  {test_file} not found, skipping")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"\n📊 Critical Tests: {passed}/{len(results)} passed")
    return failed == 0

def run_performance_tests():
    """Run performance-focused tests"""
    print("⚡ Running Performance Tests")
    print("=" * 60)
    
    # Run tests with performance monitoring
    test_file = "test_prompt_builder_comprehensive.py"
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if os.path.exists(test_path):
        print(f"Running {test_file} with performance monitoring...")
        
        # Run with performance markers
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v", 
            "-k", "performance",
            "--tb=short"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✅ Performance tests passed")
            print(result.stdout)
            return True
        else:
            print("❌ Performance tests failed")
            print(result.stderr)
            return False
    else:
        print(f"⚠️  {test_file} not found")
        return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            success = run_all_tests()
        elif command == "critical":
            success = run_specific_tests()
        elif command == "performance":
            success = run_performance_tests()
        else:
            print("Usage: python run_comprehensive_tests.py [all|critical|performance]")
            print("  all        - Run all tests")
            print("  critical   - Run only critical tests")
            print("  performance - Run performance tests")
            success = False
    else:
        # Default to critical tests
        success = run_specific_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
