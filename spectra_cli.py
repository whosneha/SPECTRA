#!/usr/bin/env python
"""
SPECTRA CLI entry point - ensures correct import paths
"""
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run CLI
from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
