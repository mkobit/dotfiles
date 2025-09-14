#!/usr/bin/env python3
"""Wrapper script to run pyright as a module."""

import runpy
import sys

if __name__ == "__main__":
    sys.exit(runpy.run_module("pyright", run_name="__main__"))