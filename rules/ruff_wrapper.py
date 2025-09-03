#!/usr/bin/env python3
"""Wrapper to execute ruff properly in Bazel environment."""
import os
import sys
import shutil
import tempfile

def find_real_ruff_binary():
    """Find the actual ruff binary in Bazel environment."""
    import ruff
    ruff_module_dir = os.path.dirname(ruff.__file__)
    
    # Method 1: Look in runfiles (if available)
    runfiles_dir = os.environ.get('RUNFILES_DIR', '')
    if runfiles_dir:
        possible_paths = [
            os.path.join(runfiles_dir, 'rules_python++pip+pypi_313_ruff', 'bin', 'ruff'),
            os.path.join(runfiles_dir, '_main', 'external', 'rules_python++pip+pypi_313_ruff', 'bin', 'ruff'),
        ]
        for path in possible_paths:
            if os.path.isfile(path):
                return path
    
    # Method 2: Navigate from ruff module to find external directory
    # From: .../runfiles/rules_python++pip+pypi_313_ruff/site-packages/ruff
    # To:   .../external/rules_python++pip+pypi_313_ruff/bin/ruff
    current = ruff_module_dir
    while current and current != '/':
        # Look for the pattern where we can find external directory
        if current.endswith('/execroot/_main'):
            external_base = os.path.join(current, '..', '..', 'external')
            binary_path = os.path.join(external_base, 'rules_python++pip+pypi_313_ruff', 'bin', 'ruff')
            if os.path.isfile(binary_path):
                return os.path.abspath(binary_path)
        # Also check if we're in a _bazel directory structure
        bazel_match = current.find('/_bazel/')
        if bazel_match != -1:
            # From /_bazel/hash/execroot/_main/...
            # To   /_bazel/hash/external/...
            bazel_root = current[:bazel_match + len('/_bazel/') + 32]  # hash is 32 chars
            external_base = os.path.join(bazel_root, 'external')
            binary_path = os.path.join(external_base, 'rules_python++pip+pypi_313_ruff', 'bin', 'ruff')
            if os.path.isfile(binary_path):
                return binary_path
        current = os.path.dirname(current)
    
    return None


if __name__ == "__main__":
    sys.argv[0] = "ruff"
    
    try:
        # Find the real binary and execute it directly
        # This bypasses all the Python wrapper complexity
        real_binary = find_real_ruff_binary()
        if not real_binary:
            raise FileNotFoundError("Could not find ruff binary in Bazel environment")
        
        
        # Execute the binary directly with os.execvp for Unix systems
        # This replaces the current process with ruff
        if sys.platform == "win32":
            import subprocess
            result = subprocess.run([real_binary] + sys.argv[1:])
            sys.exit(result.returncode)
        else:
            os.execvp(real_binary, [real_binary] + sys.argv[1:])
            
    except Exception as e:
        print(f"Error running ruff: {e}", file=sys.stderr)
        sys.exit(1)