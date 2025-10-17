#!/usr/bin/env python3
"""
TEST RUNNER FOR URBAN MOBILITY BACKEND SYSTEM

Automatically discovers and runs all test files in the src/tests/ directory.
Provides detailed reporting and summary of test results.

Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py --file <name>   # Run specific test file
    python run_tests.py --verbose       # Run with verbose output
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime
import time


class TestRunner:
    """Discovers and runs all tests in the src/tests directory."""

    def __init__(self, tests_dir="src/tests", verbose=False):
        self.tests_dir = Path(tests_dir)
        self.verbose = verbose
        self.total_files = 0
        self.passed_files = 0
        self.failed_files = 0
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def discover_test_files(self, specific_file=None):
        """Discover all test files in the tests directory."""
        if specific_file:
            # Run specific file
            test_file = self.tests_dir / specific_file
            if not test_file.exists():
                test_file = Path(specific_file)
            if test_file.exists() and test_file.suffix == ".py":
                return [test_file]
            else:
                print(f"❌ Error: Test file '{specific_file}' not found")
                return []

        # Discover all test files
        if not self.tests_dir.exists():
            print(f"❌ Error: Tests directory '{self.tests_dir}' not found")
            return []

        test_files = list(self.tests_dir.glob("*test*.py"))
        test_files.sort()
        return test_files

    def load_and_run_test_file(self, test_file):
        """Load and execute a single test file."""
        print(f"\n{'=' * 80}")
        print(f"📁 Running: {test_file.name}")
        print(f"{'=' * 80}")

        file_start_time = time.time()

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(test_file.stem, test_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module from {test_file}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[test_file.stem] = module

            # Execute the module
            spec.loader.exec_module(module)

            # Look for run_all_tests() function or __main__ execution
            if hasattr(module, "run_all_tests"):
                module.run_all_tests()
            elif hasattr(module, "test_results"):
                # Module executed tests during import
                pass
            else:
                print(f"⚠️  Warning: No test runner found in {test_file.name}")

            # Extract test results if available
            if hasattr(module, "test_results"):
                results = module.test_results
                file_end_time = time.time()
                file_duration = file_end_time - file_start_time

                self.total_files += 1
                self.total_tests += results.get("total", 0)
                self.total_passed += results.get("passed", 0)
                self.total_failed += results.get("failed", 0)

                if results.get("failed", 0) == 0:
                    self.passed_files += 1
                    status = "✅ PASSED"
                else:
                    self.failed_files += 1
                    status = "❌ FAILED"

                self.test_results.append(
                    {
                        "file": test_file.name,
                        "status": status,
                        "total": results.get("total", 0),
                        "passed": results.get("passed", 0),
                        "failed": results.get("failed", 0),
                        "errors": results.get("errors", []),
                        "duration": file_duration,
                    }
                )

                print(f"\n{status} - {test_file.name}")
                print(f"   Tests: {results['passed']}/{results['total']} passed")
                print(f"   Duration: {file_duration:.2f}s")

            else:
                print(f"⚠️  Warning: No test results found in {test_file.name}")

        except Exception as e:
            file_end_time = time.time()
            file_duration = file_end_time - file_start_time

            print(f"\n❌ ERROR running {test_file.name}: {e}")
            import traceback

            if self.verbose:
                traceback.print_exc()

            self.total_files += 1
            self.failed_files += 1

            self.test_results.append(
                {
                    "file": test_file.name,
                    "status": "❌ ERROR",
                    "total": 0,
                    "passed": 0,
                    "failed": 1,
                    "errors": [str(e)],
                    "duration": file_duration,
                }
            )

    def print_summary(self):
        """Print comprehensive test summary."""
        total_duration = (self.end_time or 0.0) - (self.start_time or 0.0)

        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)

        # File-level summary
        print(f"\n📁 Test Files:")
        print(f"   Total:  {self.total_files}")
        print(f"   ✅ Passed: {self.passed_files}")
        print(f"   ❌ Failed: {self.failed_files}")

        # Test-level summary
        print(f"\n🧪 Individual Tests:")
        print(f"   Total:  {self.total_tests}")
        print(f"   ✅ Passed: {self.total_passed}")
        print(f"   ❌ Failed: {self.total_failed}")

        # Calculate success rate
        if self.total_tests > 0:
            success_rate = (self.total_passed / self.total_tests) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")

        # Duration
        print(f"\n⏱️  Total Duration: {total_duration:.2f}s")

        # Detailed results per file
        if self.test_results:
            print(f"\n📋 Detailed Results:")
            for result in self.test_results:
                print(f"\n   {result['status']} {result['file']}")
                print(
                    f"      Tests: {result['passed']}/{result['total']} passed, {result['failed']} failed"
                )
                print(f"      Duration: {result['duration']:.2f}s")

                if result["errors"] and self.verbose:
                    print(f"      Errors:")
                    for error in result["errors"][:5]:  # Show first 5 errors
                        print(f"         • {error}")
                    if len(result["errors"]) > 5:
                        print(
                            f"         ... and {len(result['errors']) - 5} more errors"
                        )

        # Final status
        print("\n" + "=" * 80)
        if self.failed_files == 0 and self.total_failed == 0:
            print("✅ ALL TESTS PASSED! 🎉")
        else:
            print(f"❌ {self.failed_files} FILE(S) FAILED WITH {self.total_failed} TEST FAILURES")

        print("=" * 80)

    def run(self, specific_file=None):
        """Run all discovered tests."""
        print("\n" + "🧪" * 40)
        print("TEST RUNNER - URBAN MOBILITY BACKEND SYSTEM")
        print(f"Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🧪" * 40)

        self.start_time = time.time()

        # Discover test files
        test_files = self.discover_test_files(specific_file)

        if not test_files:
            print("\n❌ No test files found!")
            return 1

        print(f"\n📋 Discovered {len(test_files)} test file(s):")
        for test_file in test_files:
            print(f"   • {test_file.name}")

        # Run each test file
        for test_file in test_files:
            self.load_and_run_test_file(test_file)

        self.end_time = time.time()

        # Print summary
        self.print_summary()

        # Return exit code (0 = success, 1 = failure)
        return 0 if self.failed_files == 0 and self.total_failed == 0 else 1


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run all tests for Urban Mobility Backend System"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Run specific test file (e.g., comprehensive_tests.py)",
        default=None,
    )
    parser.add_argument(
        "--verbose", "-v", help="Enable verbose output", action="store_true"
    )
    parser.add_argument(
        "--dir",
        "-d",
        help="Tests directory (default: src/tests)",
        default="src/tests",
    )

    args = parser.parse_args()

    # Create and run test runner
    runner = TestRunner(tests_dir=args.dir, verbose=args.verbose)
    exit_code = runner.run(specific_file=args.file)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
