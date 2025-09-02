#!/usr/bin/env python3
"""JSON merge and patch tool using jsonpatch library."""

import argparse
import json
import sys
from typing import Any, Dict

try:
    import jsonpatch
except ImportError:
    print("Error: jsonpatch library not found", file=sys.stderr)
    sys.exit(1)


def deep_merge(base: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge src into base, returning a new dict."""
    result = base.copy()
    
    for key, value in src.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result


def main():
    parser = argparse.ArgumentParser(description="Merge or patch JSON files")
    parser.add_argument("--base", required=True, help="Base JSON file")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--merge", action="store_true", help="Merge mode: deep merge base with src")
    parser.add_argument("--src", help="Source JSON file to merge (merge mode only)")
    parser.add_argument("patches", nargs="*", help="JSON patch files to apply (patch mode only)")
    
    args = parser.parse_args()
    
    # Load base document
    with open(args.base, 'r') as f:
        doc = json.load(f)
    
    if args.merge:
        # Merge mode: deep merge base with src
        if not args.src:
            parser.error("--src is required when using --merge")
        
        with open(args.src, 'r') as f:
            src_doc = json.load(f)
        
        if not isinstance(doc, dict) or not isinstance(src_doc, dict):
            raise ValueError("Both base and src must be JSON objects for merging")
            
        doc = deep_merge(doc, src_doc)
    else:
        # Patch mode: apply patches in order
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