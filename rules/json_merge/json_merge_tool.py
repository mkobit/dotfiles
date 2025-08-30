#!/usr/bin/env python3
"""
JSON merge tool for dotfiles Bazel rules.

Provides deterministic JSON merging capabilities with configurable strategies,
specifically designed for Claude hooks and other JSON configuration merging.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

JsonValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def deep_merge(base: JsonValue, update: JsonValue, strategy: str = "deep_merge") -> JsonValue:
    """
    Perform deep merge of two JSON values.
    
    Args:
        base: Base JSON value
        update: JSON value to merge into base
        strategy: Merge strategy to use
    
    Returns:
        Merged JSON value
    """
    if strategy == "deep_merge":
        return _deep_merge_recursive(base, update)
    elif strategy == "claude_hooks":
        return _claude_hooks_merge(base, update)
    else:
        raise ValueError(f"Unsupported merge strategy: {strategy}")


def _deep_merge_recursive(base: JsonValue, update: JsonValue) -> JsonValue:
    """
    Recursive deep merge implementation.
    
    Strategy:
    - Dictionaries: merge recursively, update takes precedence
    - Lists: concatenate (base + update)
    - Primitives: update overwrites base
    """
    if isinstance(base, dict) and isinstance(update, dict):
        result = base.copy()
        for key, value in update.items():
            if key in result:
                result[key] = _deep_merge_recursive(result[key], value)
            else:
                result[key] = value
        return result
    elif isinstance(base, list) and isinstance(update, list):
        return base + update
    else:
        return update


def _claude_hooks_merge(base: JsonValue, update: JsonValue) -> JsonValue:
    """
    Claude hooks specific merge strategy.
    
    For Claude hooks JSON files, we want to:
    - Merge hooks objects deeply
    - Preserve all hook configurations
    - Allow override of specific tool hooks
    """
    if not isinstance(base, dict) or not isinstance(update, dict):
        return update
    
    result = base.copy()
    
    # Handle hooks object specially
    if "hooks" in base and "hooks" in update:
        if isinstance(base["hooks"], dict) and isinstance(update["hooks"], dict):
            hooks_result = base["hooks"].copy()
            for hook_type, hook_config in update["hooks"].items():
                if hook_type in hooks_result and isinstance(hooks_result[hook_type], dict) and isinstance(hook_config, dict):
                    # Merge tool configurations within hook type
                    hooks_result[hook_type].update(hook_config)
                else:
                    hooks_result[hook_type] = hook_config
            result["hooks"] = hooks_result
        else:
            result["hooks"] = update["hooks"]
    elif "hooks" in update:
        result["hooks"] = update["hooks"]
    
    # Handle other top-level keys with standard deep merge
    for key, value in update.items():
        if key != "hooks":
            if key in result:
                result[key] = _deep_merge_recursive(result[key], value)
            else:
                result[key] = value
    
    return result


def load_json_file(file_path: str) -> JsonValue:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)


def write_json_file(data: JsonValue, output_path: str, pretty: bool = True) -> None:
    """Write JSON data to file with deterministic formatting."""
    try:
        with open(output_path, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2, sort_keys=True, separators=(',', ': '))
                f.write('\n')  # Ensure trailing newline
            else:
                json.dump(data, f, sort_keys=True, separators=(',', ':'))
    except (OSError, IOError) as e:
        print(f"Error writing to {output_path}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_claude_hooks(data: JsonValue) -> bool:
    """Validate Claude hooks JSON structure."""
    if not isinstance(data, dict):
        print("Error: Root must be an object", file=sys.stderr)
        return False
    
    if "hooks" not in data:
        print("Error: Missing 'hooks' object", file=sys.stderr)
        return False
    
    hooks = data["hooks"]
    if not isinstance(hooks, dict):
        print("Error: 'hooks' must be an object", file=sys.stderr)
        return False
    
    valid_hook_types = {"PreToolUse", "PostToolUse"}
    valid_tools = {
        "Bash", "Edit", "MultiEdit", "Read", "Write", "Glob",
        "Grep", "LS", "WebFetch", "Task", "TodoWrite"
    }
    
    for hook_type, hook_config in hooks.items():
        if hook_type not in valid_hook_types:
            print(f"Warning: Unknown hook type '{hook_type}'", file=sys.stderr)
        
        if not isinstance(hook_config, dict):
            print(f"Error: Hook '{hook_type}' configuration must be an object", file=sys.stderr)
            return False
        
        for tool_name, command in hook_config.items():
            if tool_name not in valid_tools:
                print(f"Warning: Unknown tool '{tool_name}' in hook '{hook_type}'", file=sys.stderr)
            
            if not isinstance(command, str) or not command.strip():
                print(f"Error: Command for '{tool_name}' in '{hook_type}' must be a non-empty string", file=sys.stderr)
                return False
    
    return True


def merge_json_files(
    input_files: List[str],
    merge_document: str = None,
    strategy: str = "deep_merge",
    output_path: str = None,
    validate_hooks: bool = False
) -> JsonValue:
    """
    Merge multiple JSON files.
    
    Args:
        input_files: List of JSON file paths to merge
        merge_document: Optional additional JSON file to merge at the end
        strategy: Merge strategy to use
        output_path: Output file path (if None, returns merged data)
        validate_hooks: Whether to validate as Claude hooks format
    
    Returns:
        Merged JSON data
    """
    if not input_files:
        print("Error: No input files specified", file=sys.stderr)
        sys.exit(1)
    
    # Start with first file as base
    result = load_json_file(input_files[0])
    
    # Merge remaining input files
    for file_path in input_files[1:]:
        data = load_json_file(file_path)
        result = deep_merge(result, data, strategy)
    
    # Apply merge document if specified
    if merge_document:
        merge_doc = load_json_file(merge_document)
        result = deep_merge(result, merge_doc, strategy)
    
    # Validate if requested
    if validate_hooks and not validate_claude_hooks(result):
        print("Error: Validation failed", file=sys.stderr)
        sys.exit(1)
    
    # Write output if path specified
    if output_path:
        write_json_file(result, output_path)
        print(f"Successfully merged {len(input_files)} files to {output_path}")
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Merge JSON files with configurable strategies"
    )
    parser.add_argument(
        "--inputs", 
        nargs='+', 
        required=True, 
        help="Input JSON file paths to merge"
    )
    parser.add_argument(
        "--merge-document",
        help="Optional JSON merge document to apply after merging inputs"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path"
    )
    parser.add_argument(
        "--strategy",
        choices=["deep_merge", "claude_hooks"],
        default="deep_merge",
        help="Merge strategy to use"
    )
    parser.add_argument(
        "--validate-hooks",
        action="store_true",
        help="Validate output as Claude hooks format"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON (no pretty printing)"
    )
    
    args = parser.parse_args()
    
    # Perform merge
    result = merge_json_files(
        input_files=args.inputs,
        merge_document=args.merge_document,
        strategy=args.strategy,
        validate_hooks=args.validate_hooks
    )
    
    # Write output
    write_json_file(result, args.output, pretty=not args.compact)
    
    print(f"Successfully merged {len(args.inputs)} files to {args.output}")


if __name__ == "__main__":
    main()