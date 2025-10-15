"""Run all tests with coverage reporting."""
import subprocess
import sys

def run_tests():
    """Run pytest with coverage."""
    print("=" * 60)
    print("  TraceMind Test Suite")
    print("=" * 60)
    print()
    
    # Run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd="backend"
    )
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("  ✅ All tests passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  ❌ Some tests failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
