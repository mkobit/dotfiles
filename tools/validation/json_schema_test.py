#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
It's designed to be used as a pure pytest executable with proper error reporting.
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict, Any
import argparse
import sys
import os

try:
    from rules_python.python.runfiles import runfiles
    RUNFILES_AVAILABLE = True
except ImportError:
    RUNFILES_AVAILABLE = False

import jsonschema
from jsonschema import ValidationError


class JSONSchemaValidator:
    """JSON schema validator for use with pytest and bazel runfiles."""
    
    def __init__(self, schema_path: str, json_paths: List[str]):
        self.schema_path = schema_path
        self.json_paths = json_paths
        self._schema = None
        self._runfiles = None
        
        if RUNFILES_AVAILABLE:
            self._runfiles = runfiles.Create()
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path using runfiles if available, otherwise use as-is."""
        if self._runfiles:
            resolved = self._runfiles.Rlocation(path)
            if resolved:
                return Path(resolved)
        return Path(path)
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Load and cache the JSON schema."""
        if self._schema is None:
            schema_file = self._resolve_path(self.schema_path)
            assert schema_file.exists(), f"Schema file not found: {schema_file}"
            
            with open(schema_file) as f:
                self._schema = json.load(f)
                
            # Validate that we loaded a proper schema
            assert isinstance(self._schema, dict), f"Schema must be a JSON object, got {type(self._schema)}"
            
        return self._schema
    
    def load_json_file(self, json_path: str) -> Dict[str, Any]:
        """Load and parse a JSON file with detailed error reporting."""
        json_file = self._resolve_path(json_path)
        
        assert json_file.exists(), f"JSON file not found: {json_file}"
        
        try:
            with open(json_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file}: {e}")
        except Exception as e:
            pytest.fail(f"Failed to read {json_file}: {e}")
            
        return data
    
    def validate_file(self, json_path: str) -> None:
        """Validate a single JSON file against the schema with detailed assertions."""
        # Load the JSON data
        data = self.load_json_file(json_path)
        
        # Perform schema validation with detailed error reporting
        try:
            jsonschema.validate(data, self.schema)
        except ValidationError as e:
            # Create a detailed error message for pytest
            error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            pytest.fail(
                f"Schema validation failed for {json_path}\n"
                f"  Location: {error_path}\n" 
                f"  Error: {e.message}\n"
                f"  Invalid value: {e.instance}\n"
                f"  Schema rule: {e.schema}"
            )
        except Exception as e:
            pytest.fail(f"Unexpected validation error for {json_path}: {e}")


# Global validator instance - initialized by environment variables
validator = None


def _get_validator():
    """Get or create the validator from environment variables."""
    global validator
    if validator is None:
        schema_path = os.environ.get("PYTEST_SCHEMA")
        json_files_str = os.environ.get("PYTEST_JSON_FILES", "")
        json_files = json_files_str.split() if json_files_str else []
        
        if schema_path and json_files:
            validator = JSONSchemaValidator(schema_path, json_files)
    return validator


def pytest_generate_tests(metafunc):
    """Generate test parameters for each JSON file."""
    if "json_file_path" in metafunc.fixturenames:
        v = _get_validator()
        if v is None:
            # Skip if no validator configured
            metafunc.parametrize("json_file_path", [], ids=[])
        else:
            metafunc.parametrize("json_file_path", v.json_paths, ids=lambda x: Path(x).name)


def test_json_file_exists(json_file_path):
    """Test that the JSON file exists and is readable."""
    v = _get_validator()
    resolved_path = v._resolve_path(json_file_path)
    assert resolved_path.exists(), f"JSON file does not exist: {resolved_path}"
    assert resolved_path.is_file(), f"Path is not a file: {resolved_path}"


def test_json_file_syntax(json_file_path):
    """Test that the JSON file has valid syntax."""
    v = _get_validator()
    data = v.load_json_file(json_file_path)
    assert data is not None, f"JSON file {json_file_path} loaded as None"


def test_json_schema_validation(json_file_path):
    """Test that the JSON file validates against the schema."""
    v = _get_validator()
    v.validate_file(json_file_path)


def main():
    """Entry point for bazel test execution."""
    global validator
    
    # Parse our custom arguments first, before pytest sees them
    parser = argparse.ArgumentParser(description="Validate JSON files against a schema using pytest")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    parser.add_argument("files", nargs="+", help="JSON files to validate")
    
    args, remaining_args = parser.parse_known_args()
    
    # Set up environment for pytest configuration
    os.environ["PYTEST_SCHEMA"] = args.schema  
    os.environ["PYTEST_JSON_FILES"] = " ".join(args.files)
    
    # Initialize validator for pytest
    validator = JSONSchemaValidator(args.schema, args.files)
    
    # Run pytest with our file and any remaining arguments
    pytest_args = [__file__, "-v", "--tb=short"] + remaining_args
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()