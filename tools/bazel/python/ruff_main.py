#!/usr/bin/env python3
"""Wrapper script to run ruff using Python module execution."""

import sys
import subprocess

def main():
    # Use python -m ruff to run ruff as a module
    result = subprocess.run([sys.executable, "-m", "ruff"] + sys.argv[1:])
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())