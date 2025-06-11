import subprocess
import sys


def run_tests():
    """Run RBAC tests with proper output"""
    print("🔐 Running Urban Mobility RBAC Test Suite...")
    print("=" * 50)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print("✅ All tests passed! RBAC system is secure.")
        else:
            print("❌ Some tests failed. Check output above.")

    except Exception as e:
        print(f"Error running tests: {e}")


if __name__ == "__main__":
    run_tests()
