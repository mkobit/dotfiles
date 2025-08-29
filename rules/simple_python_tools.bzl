"""
Simplified Python tooling rules using run_shell approach.

This replaces the complex 360+ line implementation with simple shell actions
that leverage the Python toolchain and pip dependencies directly.
"""

def python_ruff_format_test(name, srcs, **kwargs):
    """Test that Python files are formatted correctly with ruff."""
    native.run_shell(
        name = name,
        srcs = srcs,
        cmd = "$(location @python//:python_bin) -m ruff format --check $(locations :srcs)",
        tools = ["@python//:python_bin"],
        deps = ["@pypi//ruff"],
        **kwargs
    )

def python_ruff_check_test(name, srcs, **kwargs):
    """Test that Python files pass ruff linting."""
    native.run_shell(
        name = name,
        srcs = srcs,
        cmd = "$(location @python//:python_bin) -m ruff check $(locations :srcs)",
        tools = ["@python//:python_bin"],
        deps = ["@pypi//ruff"],
        **kwargs
    )

def python_mypy_test(name, srcs, **kwargs):
    """Test that Python files pass mypy type checking."""
    native.run_shell(
        name = name,
        srcs = srcs,
        cmd = "$(location @python//:python_bin) -m mypy --ignore-missing-imports $(locations :srcs)",
        tools = ["@python//:python_bin"],
        deps = ["@pypi//mypy"],
        **kwargs
    )

def python_ruff_format_fix(name, srcs, **kwargs):
    """Format Python files with ruff (modifies files in place)."""
    native.run_shell(
        name = name,
        srcs = srcs,
        cmd = "$(location @python//:python_bin) -m ruff format $(locations :srcs)",
        tools = ["@python//:python_bin"],
        deps = ["@pypi//ruff"],
        **kwargs
    )

def python_ruff_fix(name, srcs, **kwargs):
    """Auto-fix Python files with ruff (modifies files in place)."""
    native.run_shell(
        name = name,
        srcs = srcs,
        cmd = "$(location @python//:python_bin) -m ruff check --fix $(locations :srcs)",
        tools = ["@python//:python_bin"],
        deps = ["@pypi//ruff"],
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