#!/usr/bin/env python3
"""
Wrapper scripts for Python tooling executables.

These wrappers allow us to use ruff, mypy etc. as executable targets in Bazel.
"""

import sys
import subprocess


def ruff_wrapper():
    """Wrapper for ruff executable."""
    # Import ruff and run it
    try:
        import ruff.main
        return ruff.main.main()
    except ImportError:
        print("Error: ruff not available", file=sys.stderr)
        return 1


def mypy_wrapper():
    """Wrapper for mypy executable."""
    # Import mypy and run it
    try:
        import mypy.main
        return mypy.main.main(None)
    except ImportError:
        print("Error: mypy not available", file=sys.stderr)
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python_wrappers.py <tool> [args...]", file=sys.stderr)
        sys.exit(1)
    
    tool = sys.argv[1]
    # Remove the tool name from sys.argv
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    if tool == 'ruff':
        sys.exit(ruff_wrapper())
    elif tool == 'mypy':
        sys.exit(mypy_wrapper())
    else:
        print(f"Unknown tool: {tool}", file=sys.stderr)
        sys.exit(1)