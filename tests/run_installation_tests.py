#!/usr/bin/env python
"""
Quick installation test runner.

Run this to validate your SPECTRA installation:
    python tests/run_installation_tests.py

Or use pytest directly:
    pytest tests/test_installation.py -v
"""

import subprocess
import sys

def main():
    print("=" * 70)
    print("SPECTRA Installation Tests")
    print("=" * 70)
    print()

    # Run installation tests
    print("Running dependency and core import checks...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_installation.py", 
         "-v", "--tb=short", "-x"],
        cwd="."
    )

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("SUCCESS: All installation tests passed!")
        print()
        print("Your SPECTRA installation is working correctly.")
        print()
        print("Next steps:")
        print("  1. Try a quick ML fit:")
        print("     ./bin/spectra --config example_configs/config_phangs.yaml --max-rows 1 --method ml")
        print()
        print("  2. Or use Python directly:")
        print("     python run.py example_configs/config_phangs.yaml")
        print()
        print("For more info, see docs/: https://github.com/whosneha/SPECTRA/tree/main/docs")
    else:
        print("FAILED: Some installation tests did not pass.")
        print("Check the output above for details.")
    print("=" * 70)

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
