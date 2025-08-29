"""
Test file for simplified Python tooling approach using run_shell.

This replaces the 360+ lines of custom Bazel rules with simple shell actions
that leverage the Python toolchain and pip dependencies directly.
"""

load("@rules_python//python:defs.bzl", "py_library")

# Test with a simple Python file
py_library(
    name = "sample_python",
    srcs = ["sample.py"],
)

# Simple ruff format using run_shell
run_shell(
    name = "ruff_format_test",
    srcs = ["sample.py"],
    cmd = "$(location @python//:python_bin) -m ruff format --check $<",
    tools = ["@python//:python_bin"],
    deps = ["@pypi//ruff"],
)

# Simple ruff check using run_shell
run_shell(
    name = "ruff_check_test",
    srcs = ["sample.py"],
    cmd = "$(location @python//:python_bin) -m ruff check $<",
    tools = ["@python//:python_bin"],
    deps = ["@pypi//ruff"],
)

# Simple mypy check using run_shell
run_shell(
    name = "mypy_check_test",
    srcs = ["sample.py"],
    cmd = "$(location @python//:python_bin) -m mypy --ignore-missing-imports $<",
    tools = ["@python//:python_bin"],
    deps = ["@pypi//mypy"],
)

# Ruff format action that can modify files
run_shell(
    name = "ruff_format_fix",
    srcs = ["sample.py"],
    cmd = "$(location @python//:python_bin) -m ruff format $<",
    tools = ["@python//:python_bin"],
    deps = ["@pypi//ruff"],
)
