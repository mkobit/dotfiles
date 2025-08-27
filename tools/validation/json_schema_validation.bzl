"""
Simple macro for JSON schema validation using py_test.

This provides a clean interface using standard bazel py_test rules
instead of complex custom rule implementations.
"""

load("@rules_python//python:defs.bzl", "py_test")

def json_schema_validation_test(name, srcs, schema, deps = None, **kwargs):
    """
    Creates a py_test that validates JSON files against a schema.

    Args:
        name: Name of the test target
        srcs: List of JSON files to validate
        schema: JSON schema file to validate against
        deps: Additional Python dependencies
        **kwargs: Additional arguments passed to py_test
    """
    if deps == None:
        deps = []

    # For now, we'll use the existing Python installation
    # Later we can add @pypi//jsonschema when requirements are set up

    py_test(
        name = name,
        srcs = ["//tools/validation:json_schema_test.py"],
        main = "//tools/validation:json_schema_test.py",
        args = [
            "--schema",
            "$(location {})".format(schema),
        ] + ["$(location {})".format(src) for src in srcs],
        data = srcs + [schema],
        deps = deps,
        python_version = "PY3",
        **kwargs
    )
