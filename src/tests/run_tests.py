import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run Urban Mobility test suite with automatic path detection"""

    print("🔐 Urban Mobility Comprehensive Test Suite")
    print("=" * 50)

    # Get the correct paths
    project_root = get_project_root()
    tests_path = get_tests_path()

    print(f"📁 Project root: {project_root}")
    print(f"📂 Tests path: {tests_path}")

    # Verify tests directory exists
    if not os.path.exists(tests_path):
        print(f"❌ Tests directory not found: {tests_path}")
        print("💡 Make sure you have the correct directory structure")
        return False

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Test type selection with automatic path detection
    if test_type == "unit":
        unit_path = os.path.join(tests_path, "unit")
        cmd.extend([unit_path])
        print("📋 Running Unit Tests Only...")
    elif test_type == "integration":
        integration_path = os.path.join(tests_path, "integration")
        cmd.extend([integration_path])
        print("🔗 Running Integration Tests Only...")
    elif test_type == "security":
        security_path = os.path.join(tests_path, "security")
        cmd.extend([security_path])
        print("🛡️ Running Security Tests Only...")
    elif test_type == "legacy":
        legacy_path = os.path.join(tests_path, "legacy")
        cmd.extend([legacy_path])
        print("📦 Running Legacy Tests Only...")
    elif test_type == "backup":
        # Run all backup-related tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-m",
                "backup",
            ]
        )
        print("💾 Running Backup System Tests Only...")
    elif test_type == "backup_unit":
        # Run only backup unit tests
        cmd.extend([os.path.join(tests_path, "unit"), "-m", "backup_unit"])
        print("🧪 Running Backup Unit Tests Only...")
    elif test_type == "backup_integration":
        # Run only backup integration tests
        cmd.extend(
            [os.path.join(tests_path, "integration"), "-m", "backup_integration"]
        )
        print("🔗 Running Backup Integration Tests Only...")
    elif test_type == "backup_security":
        # Run only backup security tests
        cmd.extend([os.path.join(tests_path, "security"), "-m", "backup_security"])
        print("🛡️ Running Backup Security Tests Only...")
    elif test_type == "backup_menu":
        # Run only backup menu tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                "-m",
                "backup_menu",
            ]
        )
        print("📋 Running Backup Menu Tests Only...")
    elif test_type == "encryption":
        # Exclude legacy to avoid issues
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-k",
                "encryption",
            ]
        )
        print("🔒 Running Encryption Tests Only...")
    elif test_type == "travelers":
        # Exclude legacy to avoid issues
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-k",
                "travelers",
            ]
        )
        print("👥 Running Travelers Management Tests Only...")
    elif test_type == "user_manager":
        # Run user management tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-k",
                "user_manager",
            ]
        )
        print("👤 Running User Management Tests Only...")
    elif test_type == "auth":
        # Exclude legacy to avoid issues
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-k",
                "auth",
            ]
        )
        print("🔑 Running Authentication Tests Only...")
    elif test_type == "rbac":
        # Run role-based access control tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-m",
                "rbac",
            ]
        )
        print("🔐 Running RBAC Tests Only...")
    elif test_type == "menu":
        # Run menu system tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                "-m",
                "menu",
            ]
        )
        print("📋 Running Menu System Tests Only...")
    elif test_type == "performance":
        # Run performance tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                "-m",
                "performance",
            ]
        )
        print("⚡ Running Performance Tests Only...")
    elif test_type == "fast":
        # Exclude legacy and slow tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
                "-m",
                "not slow",
            ]
        )
        print("⚡ Running Fast Tests Only...")
    elif test_type == "comprehensive":
        # Run comprehensive test suite including backup tests
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
            ]
        )
        print("🎯 Running Comprehensive Test Suite (including backup system)...")
    else:
        # Default: Run all tests EXCEPT legacy (to avoid issues)
        cmd.extend(
            [
                os.path.join(tests_path, "unit"),
                os.path.join(tests_path, "integration"),
                os.path.join(tests_path, "security"),
            ]
        )
        print("🧪 Running All Tests (excluding legacy)...")

    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.extend(["-v", "--tb=short"])

    # Add coverage if requested
    if coverage:
        cmd.extend(
            [
                "--cov=auth",
                "--cov=managers",
                "--cov=data",
                "--cov=utils",
                "--cov=models",
                "--cov=backup_menu",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )
        print("📊 Coverage reporting enabled")

    # Additional pytest options
    cmd.extend(
        [
            "--strict-markers",
            "--disable-warnings",
            "-ra",  # Show short test summary info for all tests
        ]
    )

    print(f"💻 Command: {' '.join(cmd)}")
    print("=" * 50)

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show real-time output
            text=True,
            cwd=".",
        )

        print("\n" + "=" * 50)

        if result.returncode == 0:
            print("✅ ALL TESTS PASSED!")
            print("🎉 Urban Mobility system is secure and functional!")
            if coverage:
                print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔍 Please check the output above for details.")
            return False

        return True

    except FileNotFoundError:
        print("❌ Error: pytest not found!")
        print("💡 Install pytest: pip install pytest pytest-cov")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test_file(test_file, verbose=False):
    """Run a specific test file"""

    print(f"🎯 Running Specific Test: {test_file}")
    print("=" * 50)

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_file,
        "-v" if verbose else "-v",
        "--tb=short",
    ]

    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=".")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def check_test_environment():
    """Check if test environment is properly set up"""

    print("🔍 Checking Test Environment...")
    print("=" * 30)

    issues = []

    # Check for pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ pytest is installed")
        else:
            issues.append("pytest not working properly")
    except FileNotFoundError:
        issues.append("pytest not installed")

    # Check test directories
    test_dirs = ["tests/unit", "tests/integration", "tests/security"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"✅ {test_dir} directory exists")
        else:
            issues.append(f"{test_dir} directory missing")

    # Check key test files including backup tests
    key_files = [
        "tests/unit/test_encryption_unit.py",
        "tests/unit/test_travelers_manager_unit.py",
        "tests/unit/test_user_manager_unit.py",
        "tests/unit/test_backup_manager_unit.py",
        "tests/integration/test_travelers_integration.py",
        "tests/integration/test_user_manager_integration.py",
        "tests/integration/test_backup_integration.py",
        "tests/security/test_travelers_security.py",
        "tests/security/test_user_manager_security.py",
        "tests/security/test_backup_security.py",
        "tests/integration/test_backup_menu_integration.py",
    ]

    for test_file in key_files:
        if os.path.exists(test_file):
            print(f"✅ {test_file} exists")
        else:
            issues.append(f"{test_file} missing")

    # Check for source code including backup system
    source_files = [
        "auth.py",
        "managers/travelers_manager.py",
        "managers/user_manager.py",
        "managers/backup_manager.py",
        "data/encryption.py",
        "backup_menu.py",
    ]

    for source_file in source_files:
        if os.path.exists(source_file):
            print(f"✅ {source_file} exists")
        else:
            issues.append(f"{source_file} missing")

    print("=" * 30)

    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 Please fix these issues before running tests")
        return False
    else:
        print("🎉 Test environment is ready!")
        return True


def create_test_report():
    """Generate a comprehensive test report"""

    print("📋 Generating Comprehensive Test Report...")
    print("=" * 50)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--tb=short",
        "-v",
        "--junit-xml=test_report.xml",
        "--html=test_report.html",
        "--self-contained-html",
    ]

    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=".")

        print("\n" + "=" * 50)
        print("📄 Test reports generated:")
        print("   • test_report.xml (JUnit format)")
        print("   • test_report.html (HTML format)")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False


def run_backup_test_suite():
    """Run comprehensive backup system test suite"""

    print("💾 Running Comprehensive Backup System Test Suite")
    print("=" * 60)

    backup_test_categories = [
        ("backup_unit", "🧪 Backup Unit Tests"),
        ("backup_integration", "🔗 Backup Integration Tests"),
        ("backup_security", "🛡️ Backup Security Tests"),
        ("backup_menu", "📋 Backup Menu Tests"),
    ]

    results = {}

    for test_type, description in backup_test_categories:
        print(f"\n{description}")
        print("-" * 40)

        success = run_tests(test_type, verbose=False, coverage=False)
        results[test_type] = success

        if success:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")

    # Summary
    print("\n" + "=" * 60)
    print("📊 BACKUP TEST SUITE SUMMARY")
    print("=" * 60)

    total_tests = len(backup_test_categories)
    passed_tests = sum(1 for success in results.values() if success)

    for test_type, description in backup_test_categories:
        status = "✅ PASSED" if results[test_type] else "❌ FAILED"
        print(f"{description}: {status}")

    print(f"\nOverall Result: {passed_tests}/{total_tests} test categories passed")

    if passed_tests == total_tests:
        print("🎉 ALL BACKUP TESTS PASSED!")
        print("💾 Backup system is fully functional and secure!")
        return True
    else:
        print("⚠️ Some backup tests failed - please review above output")
        return False


def get_project_root():
    """Get the path to the project root directory"""
    return Path(__file__).parent.parent.absolute()


def get_tests_path():
    """Get the path to the tests directory"""
    return Path(__file__).parent.absolute()


def main():
    """Main function with command line interface"""

    parser = argparse.ArgumentParser(
        description="Urban Mobility Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                          # Run all tests
  python run_tests.py --type unit              # Run only unit tests
  python run_tests.py --type backup            # Run only backup tests
  python run_tests.py --type backup_unit       # Run only backup unit tests
  python run_tests.py --type backup_integration # Run only backup integration tests
  python run_tests.py --type backup_security   # Run only backup security tests
  python run_tests.py --type backup_menu       # Run only backup menu tests
  python run_tests.py --type security          # Run only security tests
  python run_tests.py --type user_manager      # Run only user management tests
  python run_tests.py --type comprehensive     # Run comprehensive test suite
  python run_tests.py --coverage               # Run with coverage
  python run_tests.py --verbose                # Run with verbose output
  python run_tests.py --check                  # Check test environment
  python run_tests.py --report                 # Generate test report
  python run_tests.py --backup-suite           # Run complete backup test suite
  python run_tests.py --file tests/unit/test_backup_manager_unit.py  # Run specific file
        """,
    )

    parser.add_argument(
        "--type",
        choices=[
            "all",
            "unit",
            "integration",
            "security",
            "encryption",
            "travelers",
            "user_manager",
            "auth",
            "fast",
            "comprehensive",
            "performance",
            "backup",
            "backup_unit",
            "backup_integration",
            "backup_security",
            "backup_menu",
            "rbac",
            "menu",
        ],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Enable coverage reporting"
    )

    parser.add_argument(
        "--check", action="store_true", help="Check test environment setup"
    )

    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive test report"
    )

    parser.add_argument(
        "--backup-suite",
        action="store_true",
        help="Run comprehensive backup test suite",
    )

    parser.add_argument("--file", "-f", type=str, help="Run specific test file")

    args = parser.parse_args()

    # Handle different modes
    if args.check:
        success = check_test_environment()
        sys.exit(0 if success else 1)

    if args.report:
        success = create_test_report()
        sys.exit(0 if success else 1)

    if args.backup_suite:
        success = run_backup_test_suite()
        sys.exit(0 if success else 1)

    if args.file:
        success = run_specific_test_file(args.file, args.verbose)
        sys.exit(0 if success else 1)

    # Run normal tests
    success = run_tests(args.type, args.verbose, args.coverage)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
