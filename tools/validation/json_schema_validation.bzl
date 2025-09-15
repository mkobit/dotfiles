"""
Simple macro for JSON schema validation using pytest.

This provides a clean interface using pytest with bazel runfiles
for proper test resource access.
"""

load("@rules_python//python:defs.bzl", "py_test")

def json_schema_validation_test(name, srcs, schema, deps = None, **kwargs):
    """
    Creates a pytest test that validates JSON files against a schema.

    Args:
        name: Name of the test target
        srcs: List of JSON files to validate
        schema: JSON schema file to validate against
        deps: Additional Python dependencies
        **kwargs: Additional arguments passed to py_test
    """
    if deps == None:
        deps = []

    # Add required dependencies for pytest and jsonschema
    test_deps = [
        "//build/validation:json_schema_test",
        "@pypi//pytest",
        "@pypi//jsonschema",
    ] + deps

    py_test(
        name = name,
        srcs = ["//build/validation:json_schema_test.py"],
        main = "//build/validation:json_schema_test.py",
        args = [
            "--schema",
            "$(location {})".format(schema),
            "--",
        ] + ["$(location {})".format(src) for src in srcs],
        data = srcs + [schema],
        deps = test_deps,
        python_version = "PY3",
        **kwargs
    )
