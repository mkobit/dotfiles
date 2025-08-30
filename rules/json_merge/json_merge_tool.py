#!/usr/bin/env python3
"""Simple JSON merge tool for Bazel rules."""

import argparse
import json
import sys


def deep_merge(base, update):
    """Deep merge two dictionaries."""
    if isinstance(base, dict) and isinstance(update, dict):
        result = base.copy()
        for key, value in update.items():
            if key in result:
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    elif isinstance(base, list) and isinstance(update, list):
        return base + update
    else:
        return update


def main():
    parser = argparse.ArgumentParser(description="Merge JSON files")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("inputs", nargs="+", help="Input JSON files to merge")
    
    args = parser.parse_args()
    
    # Start with first file
    with open(args.inputs[0], 'r') as f:
        result = json.load(f)
    
    # Merge remaining files
    for input_file in args.inputs[1:]:
        with open(input_file, 'r') as f:
            data = json.load(f)
        result = deep_merge(result, data)
    
    # Write output
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == "__main__":
    main()