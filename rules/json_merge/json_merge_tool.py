#!/usr/bin/env python3
"""JSON patch tool using jsonpatch library."""

import argparse
import json
import sys

try:
    import jsonpatch
except ImportError:
    print("Error: jsonpatch library not found", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Apply JSON patches using jsonpatch library")
    parser.add_argument("--base", required=True, help="Base JSON file")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("patches", nargs="*", help="JSON patch files to apply")
    
    args = parser.parse_args()
    
    # Load base document
    with open(args.base, 'r') as f:
        doc = json.load(f)
    
    # Apply patches in order
    for patch_file in args.patches:
        with open(patch_file, 'r') as f:
            patch_ops = json.load(f)
        
        if not isinstance(patch_ops, list):
            raise ValueError(f"Patch file {patch_file} must contain an array of operations")
        
        # Create and apply patch
        patch = jsonpatch.JsonPatch(patch_ops)
        doc = patch.apply(doc)
    
    # Write output
    with open(args.output, 'w') as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == "__main__":
    main()