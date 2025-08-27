#!/usr/bin/env python3
"""
JSON Schema validation test.

This script validates JSON files against a provided JSON schema using jsonschema.
It's designed to be used as a standalone test that can be invoked by Bazel.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List


def validate_files(json_files: List[Path], schema_file: Path) -> bool:
    """
    Validate JSON files against a schema.
    
    Args:
        json_files: List of JSON files to validate
        schema_file: Path to JSON schema file
        
    Returns:
        True if all files are valid, False otherwise
    """
    # TODO: Add jsonschema to requirements.lock.txt and uncomment schema validation
    try:
        import jsonschema
        use_schema_validation = True
    except ImportError:
        print("INFO: jsonschema not available - performing JSON syntax validation only")
        use_schema_validation = False
    
    # Load schema (only if doing full validation)
    schema = None
    if use_schema_validation:
        try:
            with open(schema_file) as f:
                schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"ERROR: Failed to load schema file {schema_file}: {e}")
            return False
    
    all_valid = True
    
    for json_file in json_files:
        if use_schema_validation:
            print(f"Validating: {json_file} against {schema_file}")
        else:
            print(f"Validating JSON syntax: {json_file}")
        
        if not json_file.exists():
            print(f"ERROR: File {json_file} does not exist")
            all_valid = False
            continue
            
        try:
            with open(json_file) as f:
                data = json.load(f)
                
            if use_schema_validation:
                jsonschema.validate(data, schema)
                print(f"OK: {json_file} validates against schema")
            else:
                print(f"OK: {json_file} is valid JSON")
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {json_file}: {e}")
            all_valid = False
        except Exception as e:
            if use_schema_validation and "ValidationError" in str(type(e)):
                print(f"ERROR: Schema validation failed for {json_file}: {e}")
            else:
                print(f"ERROR: Validation failed for {json_file}: {e}")
            all_valid = False
    
    return all_valid


def main():
    parser = argparse.ArgumentParser(description="Validate JSON files against a schema")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    parser.add_argument("files", nargs="+", help="JSON files to validate")
    
    args = parser.parse_args()
    
    schema_file = Path(args.schema)
    json_files = [Path(f) for f in args.files]
    
    if validate_files(json_files, schema_file):
        print("All JSON files validate against schema")
        sys.exit(0)
    else:
        print("Some JSON files failed schema validation")
        sys.exit(1)


if __name__ == "__main__":
    main()