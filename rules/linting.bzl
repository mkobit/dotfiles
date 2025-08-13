"""
Hermetic linting and formatting rules for the dotfiles project.

This module provides buildifier formatting and testing functionality
using the buildifier_prebuilt module for hermetic builds.
"""

load("@buildifier_prebuilt//:rules.bzl", "buildifier", "buildifier_test")

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
        **kwargs
    )
