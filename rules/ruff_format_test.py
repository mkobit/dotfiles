#!/usr/bin/env python3
"""Test script to check if Python files are formatted with ruff."""
import sys
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: ruff_format_test.py <file1> [file2] ...")
        sys.exit(1)
    
    files = sys.argv[1:]
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check"] + files,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Ruff format check failed:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
        
        print(f"✓ Ruff format check passed for {len(files)} files")
    
    except Exception as e:
        print(f"Error running ruff format check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()