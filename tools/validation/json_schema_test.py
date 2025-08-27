#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
It's designed to be used as a pytest test that can be invoked by Bazel with runfiles.
"""

import json
import pytest
from pathlib import Path
from typing import List
import argparse
import sys

try:
    from rules_python.python.runfiles import runfiles
    RUNFILES_AVAILABLE = True
except ImportError:
    RUNFILES_AVAILABLE = False

import jsonschema


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
    def schema(self):
        """Load and cache the JSON schema."""
        if self._schema is None:
            schema_file = self._resolve_path(self.schema_path)
            with open(schema_file) as f:
                self._schema = json.load(f)
        return self._schema
    
    def validate_file(self, json_path: str) -> None:
        """Validate a single JSON file against the schema."""
        json_file = self._resolve_path(json_path)
        
        # Load and parse JSON
        with open(json_file) as f:
            data = json.load(f)
        
        # Validate against schema
        jsonschema.validate(data, self.schema)


# Global validator instance - set by main()
validator = None


def pytest_generate_tests(metafunc):
    """Generate test parameters for each JSON file."""
    if "json_file" in metafunc.fixturenames:
        if validator is None:
            # Fallback for when pytest is run directly
            metafunc.parametrize("json_file", [])
        else:
            metafunc.parametrize("json_file", validator.json_paths)


def test_json_schema_validation(json_file):
    """Test that validates each JSON file against the schema."""
    validator.validate_file(json_file)


def main():
    """Entry point for bazel test execution."""
    global validator
    
    parser = argparse.ArgumentParser(description="Validate JSON files against a schema using pytest")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    parser.add_argument("files", nargs="+", help="JSON files to validate")
    
    args = parser.parse_args()
    
    # Initialize the validator
    validator = JSONSchemaValidator(args.schema, args.files)
    
    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()