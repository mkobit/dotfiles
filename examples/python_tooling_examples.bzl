"""
Example BUILD file configurations for the Python tooling approaches.

This demonstrates:
1. Per-target approach (recommended for simplicity)
2. Aspect-based approach (for automatic application)
"""

# Per-target approach - explicit, simple, maintainable
def example_per_target_setup():
    """Example of per-target Python quality setup."""

    # Load the simplified per-target rules
    load("//rules:simple_per_target_python.bzl", "python_quality_tests")

    # Automatically create quality tests for all Python files in package
    python_quality_tests(
        name = "python_quality",
        # Auto-discovers Python files, excluding test files
    )

    # Or manually specify files
    python_quality_tests(
        name = "manual_python_quality",
        srcs = [
            "my_module.py",
            "other_module.py",
        ],
        tags = ["python-quality"],
    )

# Aspect-based approach - automatic application
def example_aspect_setup():
    """Example of aspect-based Python quality setup."""

    # Load the aspect-based rules
    load("//rules:python_aspects.bzl", "python_quality_suite")

    # Automatically apply aspects to all Python targets in package
    python_quality_suite(
        name = "python_aspects_test",
        # Auto-discovers py_library, py_binary, py_test targets
    )

    # Or manually specify targets
    python_quality_suite(
        name = "manual_aspects_test",
        targets = [
            ":my_python_lib",
            ":my_python_binary",
        ],
    )

# Usage in BUILD.bazel:
"""
# At the top of your BUILD.bazel file:
load("//examples:python_tooling_examples.bzl", "example_per_target_setup")

# Then call the setup function:
example_per_target_setup()

# This creates these test targets:
# - :python_quality (test suite)  
# - :python_quality_format (ruff format test)
# - :python_quality_lint (ruff lint test) 
# - :python_quality_types (mypy test)

# Run with:
# bazel test :python_quality
# bazel test :python_quality_format
# bazel test :python_quality_lint  
# bazel test :python_quality_types
"""
