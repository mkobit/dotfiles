#!/usr/bin/env python3
"""
JSON Schema validation test using pytest.

This module validates JSON files against a provided JSON schema using jsonschema.
Uses explicit --schema argument with parametrized JSON files.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft7Validator, ValidationError

# Global variables to store arguments parsed manually
_GLOBAL_SCHEMA_PATH: Path | None = None
_GLOBAL_JSON_FILES: list[Path] = []


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for each JSON file passed after -- separator."""
    if "json_file" in metafunc.fixturenames:
        import os

        schema = os.environ.get("TEST_SCHEMA_PATH")
        files = os.environ.get("TEST_JSON_FILES")

        if schema and files:
            global _GLOBAL_SCHEMA_PATH, _GLOBAL_JSON_FILES
            _GLOBAL_SCHEMA_PATH = Path(schema)
            # Handle potential empty strings in split if needed
            _GLOBAL_JSON_FILES = [Path(f) for f in files.split(os.pathsep) if f]

        if not _GLOBAL_JSON_FILES:
            pytest.fail("No JSON files provided for validation (env vars not set?)")

        metafunc.parametrize("json_file", _GLOBAL_JSON_FILES)


def test_schema_validation() -> None:
    """Test that the schema file exists, is valid JSON, and is a valid JSON schema."""
    if _GLOBAL_SCHEMA_PATH is None:
        pytest.fail("Schema path not provided")

    # Assert valid path for mypy
    assert _GLOBAL_SCHEMA_PATH is not None
    schema_file = _GLOBAL_SCHEMA_PATH

    assert schema_file.exists(), f"Schema file not found: {schema_file}"
    assert schema_file.is_file(), f"Schema path is not a file: {schema_file}"

    try:
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file contains invalid JSON: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read schema file: {e}")

    assert isinstance(schema, dict), (
        f"Schema must be a JSON object, got {type(schema).__name__}"
    )

    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Schema file is not a valid JSON schema: {e}")


def test_json_file_validation(json_file: Path) -> None:
    """Test that JSON file exists, is valid JSON, and validates against the schema."""
    if _GLOBAL_SCHEMA_PATH is None:
        pytest.fail("Schema path not provided")

    # Assert valid path for mypy
    assert _GLOBAL_SCHEMA_PATH is not None
    schema_file = _GLOBAL_SCHEMA_PATH

    # Skip if schema is invalid
    try:
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)
        Draft7Validator.check_schema(schema)
    except Exception as e:
        pytest.skip(f"Skipping validation - schema is invalid: {e}")

    # Validate JSON file
    assert json_file.exists(), f"JSON file not found: {json_file}"
    assert json_file.is_file(), f"JSON path is not a file: {json_file}"

    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON file contains invalid JSON: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read JSON file: {e}")

    # Validate against schema
    try:
        jsonschema.validate(data, schema)
    except ValidationError as e:
        error_path = (
            " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        )
        pytest.fail(
            f"Schema validation failed for {json_file}\n"
            f"  Location: {error_path}\n"
            f"  Error: {e.message}\n"
            f"  Invalid value: {e.instance}"
        )
    except Exception as e:
        pytest.fail(f"Unexpected validation error for {json_file}: {e}")


if __name__ == "__main__":
    import os

    # Manual argument parsing
    args = sys.argv[1:]

    # Extract schema path
    schema_path_str = None
    try:
        if "--schema" in args:
            idx = args.index("--schema")
            if idx + 1 < len(args):
                schema_path_str = args[idx + 1]
    except ValueError:
        pass

    if not schema_path_str:
        print("Error: --schema argument is required", file=sys.stderr)
        sys.exit(1)

    # Extract files
    json_files_args = []
    try:
        if "--" in args:
            idx = args.index("--")
            json_files_args = args[idx + 1 :]
        else:
            skip_next = False
            for arg in args:
                if skip_next:
                    skip_next = False
                    continue
                if arg == "--schema":
                    skip_next = True
                    continue
                if not arg.startswith("-"):
                    json_files_args.append(arg)
    except ValueError:
        pass

    # Pass data via environment variables so the imported module can see them
    os.environ["TEST_SCHEMA_PATH"] = schema_path_str
    os.environ["TEST_JSON_FILES"] = os.pathsep.join(json_files_args)

    # Run pytest on this file only
    sys.exit(pytest.main([__file__]))
