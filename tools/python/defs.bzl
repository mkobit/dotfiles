"""Public Python tooling rules for building CLI tools.

This module provides macros for creating Python CLI tools that can be:
- Built and tested with Bazel
- Deployed as standalone zipapp executables via chezmoi

Example usage:
    load("//tools/python:defs.bzl", "python_cli_tool")

    python_cli_tool(
        name = "my_tool",
        main = "main.py",
        srcs = ["lib.py"],
        deps = ["@pypi//click"],
        test_srcs = ["lib_test.py"],
    )
"""

load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_test")
load("//tools/python/private:zipapp.bzl", "python_zipapp")

def python_cli_tool(
        name,
        main,
        srcs = [],
        deps = [],
        data = [],
        test_srcs = [],
        test_deps = [],
        visibility = None,
        tags = []):
    """Creates a Python CLI tool with binary, test, and zipapp targets.

    This macro generates:
    - {name}: py_binary for direct execution via `bazel run`
    - {name}_exe: Standalone zipapp executable with shebang
    - {name}_test: Test target (if test_srcs provided)

    Args:
        name: Base name for the tool
        main: Main Python file (entry point)
        srcs: Additional source files
        deps: Dependencies (use @pypi//package for pip deps)
        data: Data files
        test_srcs: Test source files
        test_deps: Additional test dependencies
        visibility: Visibility specification
        tags: Tags for all targets
    """

    # Create the py_binary
    py_binary(
        name = name,
        srcs = [main] + srcs,
        main = main,
        deps = deps,
        data = data,
        visibility = visibility,
        tags = tags,
    )

    # Create the zipapp executable
    python_zipapp(
        name = name + "_exe",
        binary = ":" + name,
        visibility = visibility,
        tags = tags + ["zipapp"],
    )

    # Create test target if test sources provided
    if test_srcs:
        py_test(
            name = name + "_test",
            srcs = test_srcs,
            deps = deps + test_deps + [requirement("pytest")],
            tags = tags + ["test"],
        )
