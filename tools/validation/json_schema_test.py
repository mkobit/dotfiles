#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
Pure pytest implementation for use with bazel runfiles.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

import jsonschema
from jsonschema import ValidationError
import sys
import os

# Global state for pytest configuration
_schema_cache = None
_json_files = []


def pytest_addoption(parser):
    """Add command line options for JSON schema validation."""
    parser.addoption("--schema", action="store", required=True, 
                    help="Path to JSON schema file")


def pytest_configure(config):
    """Configure pytest with JSON files from remaining arguments."""
    global _json_files
    # Get JSON files from remaining arguments (passed after -- in pytest) 
    _json_files = config.args


def pytest_generate_tests(metafunc):
    """Generate test parameters for each JSON file."""
    if "json_file" in metafunc.fixturenames:
        if not _json_files:
            pytest.fail("No JSON files provided for validation")
        metafunc.parametrize("json_file", _json_files, ids=lambda x: Path(x).name)


def _resolve_path(path: str) -> Path:
    """Resolve a path - for now use direct path, TODO: add runfiles support."""
    return Path(path)


def _load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and cache the JSON schema."""
    global _schema_cache
    if _schema_cache is None:
        schema_file = _resolve_path(schema_path)
        assert schema_file.exists(), f"Schema file not found: {schema_file}"
        
        with open(schema_file) as f:
            _schema_cache = json.load(f)
            
        assert isinstance(_schema_cache, dict), f"Schema must be a JSON object, got {type(_schema_cache)}"
    return _schema_cache


def _load_json_file(json_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file with detailed error reporting."""
    json_file = _resolve_path(json_path)
    assert json_file.exists(), f"JSON file not found: {json_file}"
    
    try:
        with open(json_file) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {json_file}: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read {json_file}: {e}")


def test_json_file_exists(json_file, request):
    """Test that the JSON file exists and is readable."""
    resolved_path = _resolve_path(json_file)
    assert resolved_path.exists(), f"JSON file does not exist: {resolved_path}"
    assert resolved_path.is_file(), f"Path is not a file: {resolved_path}"


def test_json_file_syntax(json_file, request):
    """Test that the JSON file has valid syntax."""
    data = _load_json_file(json_file)
    assert data is not None, f"JSON file {json_file} loaded as None"


def test_json_schema_validation(json_file, request):
    """Test that the JSON file validates against the schema."""
    schema_path = request.config.getoption("--schema")
    schema = _load_schema(schema_path)
    data = _load_json_file(json_file)
    
    try:
        jsonschema.validate(data, schema)
    except ValidationError as e:
        error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        pytest.fail(
            f"Schema validation failed for {json_file}\n"
            f"  Location: {error_path}\n"
            f"  Error: {e.message}\n" 
            f"  Invalid value: {e.instance}\n"
            f"  Schema rule: {e.schema}"
        )
    except Exception as e:
        pytest.fail(f"Unexpected validation error for {json_file}: {e}")