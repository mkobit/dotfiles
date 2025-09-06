#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
Uses explicit --schema argument with parametrized JSON files.
"""

import json
import os
import pytest
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import ValidationError, Draft7Validator


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --schema command line option for JSON schema validation."""
    parser.addoption(
        "--schema",
        action="store",
        required=True,
        help="Path to JSON schema file"
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for each JSON file passed after -- separator."""
    if "json_file" in metafunc.fixturenames:
        json_files = [Path(f) for f in metafunc.config.args]
        if not json_files:
            pytest.fail("No JSON files provided for validation")
        metafunc.parametrize("json_file", json_files)


def test_schema_validation(request: pytest.FixtureRequest) -> None:
    """Test that the schema file exists, is valid JSON, and is a valid JSON schema."""
    schema_path = request.config.getoption("--schema")
    schema_file = Path(schema_path)
    
    assert schema_file.exists(), f"Schema file not found: {schema_file}"
    assert schema_file.is_file(), f"Schema path is not a file: {schema_file}"
    
    try:
        with open(schema_file, encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file contains invalid JSON: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read schema file: {e}")
    
    assert isinstance(schema, dict), f"Schema must be a JSON object, got {type(schema).__name__}"
    
    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Schema file is not a valid JSON schema: {e}")


def test_json_file_validation(json_file: Path, request: pytest.FixtureRequest) -> None:
    """Test that JSON file exists, is valid JSON, and validates against the schema."""
    json_file = "not a path"
    schema_path = request.config.getoption("--schema")
    schema_file = Path(schema_path)
    
    # Skip if schema is invalid
    try:
        with open(schema_file, encoding='utf-8') as f:
            schema = json.load(f)
        Draft7Validator.check_schema(schema)
    except Exception as e:
        pytest.skip(f"Skipping validation - schema is invalid: {e}")
    
    # Validate JSON file
    assert json_file.exists(), f"JSON file not found: {json_file}"
    assert json_file.is_file(), f"JSON path is not a file: {json_file}"
    
    try:
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON file contains invalid JSON: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read JSON file: {e}")
    
    # Validate against schema
    try:
        jsonschema.validate(data, schema)
    except ValidationError as e:
        error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        pytest.fail(
            f"Schema validation failed for {json_file}\n"
            f"  Location: {error_path}\n"
            f"  Error: {e.message}\n"
            f"  Invalid value: {e.instance}"
        )
    except Exception as e:
        pytest.fail(f"Unexpected validation error for {json_file}: {e}")

