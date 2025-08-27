#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
Uses explicit --schema argument with parametrized JSON files.
"""

import json
import pytest
import sys
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import ValidationError, Draft7Validator


def pytest_addoption(parser):
    """Add --schema command line option for JSON schema validation."""
    parser.addoption(
        "--schema", 
        action="store", 
        required=True,
        help="Path to JSON schema file"
    )


def pytest_generate_tests(metafunc):
    """Generate test parameters for each JSON file passed after -- separator."""
    if "json_file" in metafunc.fixturenames:
        # Get JSON files from pytest args (passed after -- separator)
        json_files = metafunc.config.args
        if not json_files:
            pytest.fail("No JSON files provided for validation")
        metafunc.parametrize("json_file", json_files, ids=lambda x: Path(x).name)


def validate_schema_is_valid(schema: dict[str, Any]) -> str | None:
    """Validate that a schema is itself a valid JSON schema.
    
    Returns:
        None if the schema is valid, or an error message if invalid.
    """
    try:
        # Use Draft7Validator to validate the schema itself
        Draft7Validator.check_schema(schema)
        return None
    except Exception as e:
        return f"Schema validation failed: {e}"

def load_schema(schema_path: str) -> dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(schema_path)
    assert schema_file.exists(), f"Schema file not found: {schema_file}"
    
    with open(schema_file, encoding='utf-8') as f:
        schema = json.load(f)
        
    assert isinstance(schema, dict), f"Schema must be a JSON object, got {type(schema)}"
    return schema


def load_json_file(json_path: str) -> dict[str, Any]:
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


def test_json_file_syntax(json_file, request):
    """Test that the JSON file has valid syntax."""
    # Skip this test if the schema itself is invalid
    schema_path = request.config.getoption("--schema")
    schema = load_schema(schema_path)
    schema_error = validate_schema_is_valid(schema)
    if schema_error:
        pytest.skip(f"Skipping validation because schema is invalid: {schema_error}")
    
    data = load_json_file(json_file)
    assert data is not None, f"JSON file {json_file} loaded as None"


def test_json_schema_validation(json_file, request):
    """Test that the JSON file validates against the schema."""
    schema_path = request.config.getoption("--schema")
    schema = load_schema(schema_path)
    
    # Skip this test if the schema itself is invalid
    schema_error = validate_schema_is_valid(schema)
    if schema_error:
        pytest.skip(f"Skipping validation because schema is invalid: {schema_error}")
    
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


def test_schema_is_valid_json_schema(request):
    """Test that the schema file itself is a valid JSON schema.
    
    This is an inception-like test that validates the validator.
    """
    schema_path = request.config.getoption("--schema")
    schema = load_schema(schema_path)
    
    schema_error = validate_schema_is_valid(schema)
    if schema_error:
        pytest.fail(
            f"Schema file {schema_path} is not a valid JSON schema: {schema_error}"
        )