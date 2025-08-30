"""
Test file demonstrating the improved Python tooling rules.

This shows proper usage with explicit srcs, toolchain integration,
and configuration file dependencies.
"""

load(
    "//rules:python_tooling.bzl",
    "python_mypy_test",
    "python_ruff_format",
    "python_ruff_format_test",
    "python_ruff_lint_test",
)

# Test with explicit Python source files
python_ruff_format_test(
    name = "format_check",
    srcs = [
        "//rules/common:config_generator.py",
        "//tools/validation:json_schema_test.py",
    ],
)

python_ruff_lint_test(
    name = "lint_check",
    srcs = [
        "//rules/common:config_generator.py",
        "//tools/validation:json_schema_test.py",
    ],
)

python_mypy_test(
    name = "type_check",
    srcs = [
        "//rules/common:config_generator.py",
        "//tools/validation:json_schema_test.py",
    ],
    config = "//:pyproject.toml",
)

python_ruff_format(
    name = "format_fix",
    srcs = [
        "//rules/common:config_generator.py",
        "//tools/validation:json_schema_test.py",
    ],
)
