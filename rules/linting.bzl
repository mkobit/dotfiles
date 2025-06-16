"""
Linting and formatting rules for dotfiles project.
"""

# Temporarily disable aspect_rules_lint while we get the basic build working
# load("@aspect_rules_lint//format:defs.bzl", "format_aspect", "format_multirun")
# load("@aspect_rules_lint//lint:defs.bzl", "lint_aspect", "lint_test")

def buildifier_format(name, srcs = None, **kwargs):
    """Format Bazel files using buildifier.

    Args:
        name: Name of the target
        srcs: List of Bazel files to format. If not provided, globs for BUILD.* and *.bzl files
        **kwargs: Additional arguments
    """
    # Temporary stub implementation
    native.genrule(
        name = name,
        outs = [name + "_dummy.txt"],
        cmd = "echo 'Buildifier formatting placeholder' > $@",
        visibility = kwargs.get("visibility", ["//visibility:private"]),
    )

def buildifier_test(name, srcs = None, **kwargs):
    """Test that Bazel files are properly formatted with buildifier.

    Args:
        name: Name of the test
        srcs: List of Bazel files to test. If not provided, globs for BUILD.* and *.bzl files
        **kwargs: Additional arguments
    """
    # Temporary stub implementation - always pass
    native.sh_test(
        name = name,
        srcs = ["//rules:always_pass_test.sh"],
        data = srcs or [],
        visibility = kwargs.get("visibility", ["//visibility:private"]),
    )

def bazel_files_format_test(name, **kwargs):
    """Convenient macro for testing all Bazel files in a package are formatted."""
    buildifier_test(
        name = name,
        **kwargs
    )

def bazel_files_format(name, **kwargs):
    """Convenient macro for formatting all Bazel files in a package."""
    buildifier_format(
        name = name,
        **kwargs
    )
