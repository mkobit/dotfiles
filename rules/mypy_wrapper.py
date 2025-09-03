#!/usr/bin/env python3
"""Wrapper to execute mypy properly in Bazel environment."""
import sys
import runpy

if __name__ == "__main__":
    # Execute mypy.__main__ module directly
    sys.argv[0] = "mypy"  # Set program name for help text
    try:
        runpy.run_module("mypy", run_name="__main__")
    except SystemExit as e:
        # Pass through exit codes from mypy
        sys.exit(e.code)