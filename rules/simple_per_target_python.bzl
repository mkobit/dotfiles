"""
Simplified per-target Python quality rules using py_test with direct tool invocation.

This is the cleanest approach - uses native py_test with @pypi dependencies
and simple Python test scripts for maximum maintainability.
"""

load("@rules_python//python:defs.bzl", "py_test")

def python_ruff_format_test(name, srcs, **kwargs):
    """Test that Python files are formatted correctly with ruff."""
    py_test(
        name = name,
        srcs = ["//rules:ruff_format_test.py"],
        main = "//rules:ruff_format_test.py",
        args = srcs,
        data = srcs,
        deps = ["@pypi//ruff"],
        **kwargs
    )

def python_ruff_check_test(name, srcs, **kwargs):
    """Test that Python files pass ruff linting."""
    py_test(
        name = name,
        srcs = ["//rules:ruff_check_test.py"],
        main = "//rules:ruff_check_test.py",
        args = srcs,
        data = srcs,
        deps = ["@pypi//ruff"],
        **kwargs
    )

def python_mypy_test(name, srcs, **kwargs):
    """Test that Python files pass mypy type checking."""
    py_test(
        name = name,
        srcs = ["//rules:mypy_test.py"],
        main = "//rules:mypy_test.py",
        args = srcs,
        data = srcs,
        deps = ["@pypi//mypy"],
        **kwargs
    )

def python_quality_tests(name, srcs = None, exclude_patterns = None, tags = None):
    """Create a complete suite of Python quality tests for sources.

    Args:
        name: Base name for the test suite
        srcs: List of Python source files. If None, auto-discover from glob
        exclude_patterns: Patterns to exclude from auto-discovery
        tags: Tags to apply to all tests
    """
    if srcs == None:
        if exclude_patterns == None:
            exclude_patterns = ["bazel-*/**", "**/test_*.py", "**/*_test.py"]
        srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True)

    if not srcs:
        # Create empty test_suite when no Python files exist
        native.test_suite(
            name = name,
            tests = [],
            tags = tags if tags else [],
        )
        return

    if tags == None:
        tags = []

    # Create individual test targets
    python_ruff_format_test(
        name = name + "_format",
        srcs = srcs,
        tags = tags + ["format"],
    )

    python_ruff_check_test(
        name = name + "_lint",
        srcs = srcs,
        tags = tags + ["lint"],
    )

    python_mypy_test(
        name = name + "_types",
        srcs = srcs,
        tags = tags + ["types"],
    )

    # Create test suite
    native.test_suite(
        name = name,
        tests = [
            ":" + name + "_format",
            ":" + name + "_lint",
            ":" + name + "_types",
        ],
        tags = tags,
    )
