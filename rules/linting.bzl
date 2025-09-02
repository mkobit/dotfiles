"""
Hermetic linting and formatting rules for the dotfiles project.

This module provides buildifier formatting and testing functionality
using the buildifier_prebuilt module for hermetic builds, plus Python
tooling integration.
"""

load("@buildifier_prebuilt//:rules.bzl", "buildifier", "buildifier_test")
load("//rules:simple_per_target_python.bzl", "python_quality_tests")

def bazel_files_format_test(name, exclude_patterns = None, **kwargs):
    """Test that all Bazel files are properly formatted using hermetic buildifier.

    Args:
        name: Name of the test target
        exclude_patterns: List of patterns to exclude from checking
        **kwargs: Additional attributes passed to buildifier rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "./.git/*",
            "./bazel-*",
        ]

    buildifier_test(
        name = name,
        exclude_patterns = exclude_patterns,
        lint_mode = "off",  # Turn off linting warnings for dotfiles simplicity
        mode = "diff",
        no_sandbox = True,
        workspace = "//:MODULE.bazel",
        **kwargs
    )

def bazel_files_format(name, exclude_patterns = None, **kwargs):
    """Format all Bazel files using hermetic buildifier.

    Args:
        name: Name of the formatting target
        exclude_patterns: List of patterns to exclude from formatting
        **kwargs: Additional attributes passed to buildifier rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "./.git/*",
            "./bazel-*",
        ]

    buildifier(
        name = name,
        exclude_patterns = exclude_patterns,
        lint_mode = "fix",
        mode = "fix",
        # Disable aggressive native-rule warnings for dotfiles simplicity
        lint_warnings = ["-native-sh-binary"],
        **kwargs
    )

def _unified_format_impl(ctx):
    """Implementation for unified format rule that runs all formatters."""
    script_file = ctx.actions.declare_file(ctx.label.name + "_format.sh")

    script_content = """#!/bin/bash
set -euo pipefail

echo "🔧 Running unified formatter (Bazel + Python)..."

# Run Bazel formatter via bazel command
echo "📄 Formatting Bazel files..."
bazel run {bazel_target}

# Run Python auto-fix via bazel command
echo "🐍 Auto-fixing Python files..."  
bazel run {python_target}

echo "✅ All files formatted successfully!"
""".format(
        bazel_target = ctx.attr._bazel_target,
        python_target = ctx.attr._python_target,
    )

    ctx.actions.write(
        output = script_file,
        content = script_content,
        is_executable = True,
    )

    return [DefaultInfo(
        files = depset([script_file]),
        executable = script_file,
    )]

unified_format = rule(
    implementation = _unified_format_impl,
    executable = True,
    attrs = {
        "_bazel_target": attr.string(
            default = "//:format_bazel",
        ),
        "_python_target": attr.string(
            default = "//:format_python",
        ),
    },
)

def all_files_format(name, exclude_patterns = None, **kwargs):
    """Format all supported files (Bazel + Python) in the repository.

    Args:
        name: Name of the formatting target
        exclude_patterns: List of patterns to exclude from formatting
        **kwargs: Additional attributes
    """

    # Create unified executable format target
    unified_format(name = name, **kwargs)

    # Also create individual targets for granular control
    bazel_files_format(
        name = name + "_bazel",
        exclude_patterns = exclude_patterns,
        **kwargs
    )

    # Python formatting will be handled via manual ruff run command
    # as the new simplified approach doesn't provide format targets
    native.genrule(
        name = name + "_python",
        outs = [name + "_python.log"],
        cmd = "echo 'Python formatting: Run manually with python -m ruff format .' > $@",
        **kwargs
    )

def all_files_format_test(name, exclude_patterns = None, **kwargs):
    """Test that all supported files (Bazel + Python) are properly formatted.

    Args:
        name: Name of the test target
        exclude_patterns: List of patterns to exclude from checking
        **kwargs: Additional attributes
    """

    # Test Bazel files
    bazel_files_format_test(
        name = name + "_bazel",
        exclude_patterns = exclude_patterns,
        **kwargs
    )

    # Test Python files using simplified approach
    python_quality_tests(
        name = name + "_python",
        exclude_patterns = exclude_patterns,
        **kwargs
    )
