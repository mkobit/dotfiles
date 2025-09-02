"""
Simplified Python tooling rules using sh_test approach.

This replaces the complex 360+ line implementation with simple shell tests
that leverage the Python toolchain and pip dependencies directly.
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

def python_ruff_format_test(name, srcs, **kwargs):
    """Test that Python files are formatted correctly with ruff."""
    sh_test(
        name = name,
        srcs = ["//rules:python_check_wrapper.sh"],
        data = srcs + ["//rules/common:ruff_wrapper"],
        args = ["ruff", "format", "--check"] + [("$(location %s)" % src) for src in srcs],
        **kwargs
    )

def python_ruff_check_test(name, srcs, **kwargs):
    """Test that Python files pass ruff linting."""
    sh_test(
        name = name,
        srcs = ["//rules:python_check_wrapper.sh"],
        data = srcs + ["//rules/common:ruff_wrapper"],
        args = ["ruff", "check"] + [("$(location %s)" % src) for src in srcs],
        **kwargs
    )

def python_mypy_test(name, srcs, **kwargs):
    """Test that Python files pass mypy type checking."""
    sh_test(
        name = name,
        srcs = ["//rules:python_check_wrapper.sh"],
        data = srcs + ["//rules/common:mypy_wrapper"],
        args = ["mypy", "--ignore-missing-imports"] + [("$(location %s)" % src) for src in srcs],
        **kwargs
    )

def python_ruff_format_fix(name, srcs, **kwargs):
    """Format Python files with ruff (modifies files in place)."""
    native.sh_binary(
        name = name,
        srcs = ["//rules:python_check_wrapper.sh"],
        data = srcs + ["//rules/common:ruff_wrapper"],
        args = ["ruff", "format"] + [("$(location %s)" % src) for src in srcs],
        **kwargs
    )

def python_ruff_fix(name, srcs, **kwargs):
    """Auto-fix Python files with ruff (modifies files in place)."""
    native.sh_binary(
        name = name,
        srcs = ["//rules:python_check_wrapper.sh"],
        data = srcs + ["//rules/common:ruff_wrapper"],
        args = ["ruff", "check", "--fix"] + [("$(location %s)" % src) for src in srcs],
        **kwargs
    )

# Convenience macros for common patterns
def python_files_format_test(name, exclude_patterns = None, **kwargs):
    """Test formatting on all Python files in the current package."""
    if exclude_patterns == None:
        exclude_patterns = ["bazel-*/**"]

    srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True)
    if srcs:
        python_ruff_format_test(
            name = name,
            srcs = srcs,
            **kwargs
        )

def python_files_lint_test(name, exclude_patterns = None, **kwargs):
    """Test linting on all Python files in the current package."""
    if exclude_patterns == None:
        exclude_patterns = ["bazel-*/**"]

    srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True)
    if srcs:
        python_ruff_check_test(
            name = name,
            srcs = srcs,
            **kwargs
        )

def python_files_type_test(name, exclude_patterns = None, **kwargs):
    """Test type checking on all Python files in the current package."""
    if exclude_patterns == None:
        exclude_patterns = ["bazel-*/**"]

    srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True)
    if srcs:
        python_mypy_test(
            name = name,
            srcs = srcs,
            **kwargs
        )

def python_files_fix(name, exclude_patterns = None, **kwargs):
    """Auto-fix all Python files in the current package."""
    if exclude_patterns == None:
        exclude_patterns = ["bazel-*/**"]

    srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True)
    if srcs:
        python_ruff_fix(
            name = name,
            srcs = srcs,
            **kwargs
        )
