#!/usr/bin/env python3
"""JSON patch tool for Bazel rules."""

import argparse
import json
import sys


def apply_patch_operation(doc, op):
    """Apply a single JSON patch operation to a document."""
    operation = op.get("op")
    path = op.get("path", "")
    
    if operation == "add":
        return apply_add(doc, path, op.get("value"))
    elif operation == "remove":
        return apply_remove(doc, path)
    elif operation == "replace":
        return apply_replace(doc, path, op.get("value"))
    elif operation == "test":
        return apply_test(doc, path, op.get("value"))
    else:
        raise ValueError(f"Unsupported operation: {operation}")


def parse_path(path):
    """Parse JSON pointer path into segments."""
    if not path.startswith("/"):
        raise ValueError(f"Invalid JSON pointer: {path}")
    
    if path == "/":
        return []
    
    return [segment.replace("~1", "/").replace("~0", "~") 
            for segment in path[1:].split("/")]


def get_value_at_path(doc, path_segments):
    """Get value at the specified path."""
    current = doc
    for segment in path_segments:
        if isinstance(current, dict):
            if segment not in current:
                raise KeyError(f"Path not found: {segment}")
            current = current[segment]
        elif isinstance(current, list):
            try:
                index = int(segment)
                current = current[index]
            except (ValueError, IndexError):
                raise KeyError(f"Invalid array index: {segment}")
        else:
            raise KeyError(f"Cannot index into {type(current)}")
    return current


def set_value_at_path(doc, path_segments, value):
    """Set value at the specified path."""
    if not path_segments:
        return value
    
    current = doc
    for segment in path_segments[:-1]:
        if isinstance(current, dict):
            if segment not in current:
                current[segment] = {}
            current = current[segment]
        elif isinstance(current, list):
            index = int(segment)
            current = current[index]
        else:
            raise ValueError(f"Cannot set value in {type(current)}")
    
    final_segment = path_segments[-1]
    if isinstance(current, dict):
        current[final_segment] = value
    elif isinstance(current, list):
        index = int(final_segment)
        if index == len(current):
            current.append(value)
        else:
            current[index] = value
    
    return doc


def apply_add(doc, path, value):
    """Apply add operation."""
    path_segments = parse_path(path)
    return set_value_at_path(doc, path_segments, value)


def apply_remove(doc, path):
    """Apply remove operation."""
    path_segments = parse_path(path)
    if not path_segments:
        raise ValueError("Cannot remove root")
    
    current = doc
    for segment in path_segments[:-1]:
        current = current[segment]
    
    final_segment = path_segments[-1]
    if isinstance(current, dict):
        del current[final_segment]
    elif isinstance(current, list):
        current.pop(int(final_segment))
    
    return doc


def apply_replace(doc, path, value):
    """Apply replace operation."""
    path_segments = parse_path(path)
    return set_value_at_path(doc, path_segments, value)


def apply_test(doc, path, value):
    """Apply test operation - raises exception if test fails."""
    path_segments = parse_path(path)
    try:
        actual = get_value_at_path(doc, path_segments)
        if actual != value:
            raise ValueError(f"Test failed: expected {value}, got {actual}")
    except KeyError:
        raise ValueError(f"Test failed: path {path} not found")
    return doc


def main():
    parser = argparse.ArgumentParser(description="Apply JSON patches")
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
            patch = json.load(f)
        
        if not isinstance(patch, list):
            raise ValueError(f"Patch file {patch_file} must contain an array of operations")
        
        for operation in patch:
            doc = apply_patch_operation(doc, operation)
    
    # Write output
    with open(args.output, 'w') as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == "__main__":
    main()