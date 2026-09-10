#!/usr/bin/env python
"""
SPECTRA CLI entry point - ensures correct import paths
"""
import sys
import os

# Add repo root to path
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _REPO_ROOT)

# Default SPS_HOME to the bundled FSPS data tree so python-fsps can find
# isochrones / spectra / filters without the user setting an env variable.
# Must happen BEFORE `import fsps`, which is triggered transitively by `src.cli`.
_BUNDLED_FSPS = os.path.join(_REPO_ROOT, "fsps")
if not os.environ.get("SPS_HOME") and os.path.isdir(_BUNDLED_FSPS):
    os.environ["SPS_HOME"] = _BUNDLED_FSPS

# Import and run CLI
from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
