#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
Pure pytest implementation with straightforward parameterized tests.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

import jsonschema
from jsonschema import ValidationError


def pytest_addoption(parser):
    """Add command line options for JSON schema validation."""
    parser.addoption(
        "--schema", 
        action="store", 
        required=True,
        help="Path to JSON schema file"
    )


def pytest_generate_tests(metafunc):
    """Generate test parameters for each JSON file."""
    if "json_file" in metafunc.fixturenames:
        # Get JSON files from pytest args (passed after -- separator)
        json_files = metafunc.config.args
        if not json_files:
            pytest.fail("No JSON files provided for validation")
        metafunc.parametrize("json_file", json_files, ids=lambda x: Path(x).name)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(schema_path)
    assert schema_file.exists(), f"Schema file not found: {schema_file}"
    
    with open(schema_file, encoding='utf-8') as f:
        schema = json.load(f)
        
    assert isinstance(schema, dict), f"Schema must be a JSON object, got {type(schema)}"
    return schema


def load_json_file(json_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file with detailed error reporting."""
    json_file = Path(json_path)
    assert json_file.exists(), f"JSON file not found: {json_file}"
    
    try:
        with open(json_file, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {json_file}: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read {json_file}: {e}")


def test_json_file_exists(json_file):
    """Test that the JSON file exists and is readable."""
    json_path = Path(json_file)
    assert json_path.exists(), f"JSON file does not exist: {json_path}"
    assert json_path.is_file(), f"Path is not a file: {json_path}"


def test_json_file_syntax(json_file):
    """Test that the JSON file has valid syntax."""
    data = load_json_file(json_file)
    assert data is not None, f"JSON file {json_file} loaded as None"


def test_json_schema_validation(json_file, request):
    """Test that the JSON file validates against the schema."""
    schema_path = request.config.getoption("--schema")
    schema = load_schema(schema_path)
    data = load_json_file(json_file)
    
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