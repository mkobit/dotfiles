"""
Per-target Python tooling rules.

Simple approach using py_test with inline Python scripts.
"""

load("@rules_python//python:defs.bzl", "py_test")

def python_ruff_format_test(name, srcs, **kwargs):
    """Test that Python files are formatted correctly with ruff."""
    py_test(
        name = name,
        srcs = ["//rules:ruff_format_test.py"],
        main = "//rules:ruff_format_test.py",
        args = [src for src in srcs],
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
        args = [src for src in srcs],
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
        args = [src for src in srcs],
        data = srcs,
        deps = ["@pypi//mypy"],
        **kwargs
    )
