"""
Simple linting and formatting rules for the dotfiles project.

This module provides buildifier formatting and testing functionality
that runs across all Bazel files in the repository.
"""

def buildifier_format(name, **kwargs):
    """Formats all Bazel files in the repository using buildifier.

    Args:
        name: Name of the formatting target
        **kwargs: Additional attributes passed to the underlying rule
    """
    # Create a script that runs buildifier on all Bazel files
    format_script = name + "_format_script.sh"
    native.genrule(
        name = name + "_format_script",
        outs = [format_script],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -euo pipefail

# Find buildifier binary
if command -v buildifier >/dev/null 2>&1; then
    BUILDIFIER=buildifier
elif [[ -f /usr/local/bin/buildifier ]]; then
    BUILDIFIER=/usr/local/bin/buildifier
elif [[ -f /opt/homebrew/bin/buildifier ]]; then
    BUILDIFIER=/opt/homebrew/bin/buildifier
else
    echo "buildifier not found. Please install it:"
    echo "  macOS: brew install buildifier"
    echo "  Linux: go install github.com/bazelbuild/buildtools/buildifier@latest"
    exit 1
fi

echo "Using buildifier: $$BUILDIFIER"

# Format all Bazel files in the repository
echo "Formatting all Bazel files..."
find . -name "*.bzl" -o -name "BUILD" -o -name "BUILD.bazel" | while read -r file; do
    echo "Formatting: $$file"
    "$$BUILDIFIER" -v "$$file"
done

echo "All Bazel files formatted successfully"
EOF

chmod +x $@
""",
    )

    native.sh_binary(
        name = name,
        srcs = [format_script],
        **kwargs
    )

def buildifier_test(name, **kwargs):
    """Tests that all Bazel files in the repository are properly formatted.

    Args:
        name: Name of the test target
        **kwargs: Additional attributes passed to the underlying rule
    """
    # Create a script that tests buildifier formatting
    test_script = name + "_test_script.sh"
    native.genrule(
        name = name + "_test_script",
        outs = [test_script],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -euo pipefail

# Find buildifier binary
if command -v buildifier >/dev/null 2>&1; then
    BUILDIFIER=buildifier
elif [[ -f /usr/local/bin/buildifier ]]; then
    BUILDIFIER=/usr/local/bin/buildifier
elif [[ -f /opt/homebrew/bin/buildifier ]]; then
    BUILDIFIER=/opt/homebrew/bin/buildifier
else
    echo "buildifier not found. Skipping test."
    echo "To install: brew install buildifier (macOS) or go install github.com/bazelbuild/buildtools/buildifier@latest"
    exit 0
fi

echo "Using buildifier: $$BUILDIFIER"

# Check that all Bazel files in the repository are properly formatted
echo "Checking all Bazel files for proper formatting..."
exit_code=0
find . -name "*.bzl" -o -name "BUILD" -o -name "BUILD.bazel" | while read -r file; do
    echo "Checking: $$file"
    if ! "$$BUILDIFIER" -mode=check "$$file"; then
        echo "ERROR: $$file is not properly formatted"
        echo "To fix, run: bazel run //:format"
        exit_code=1
    fi
done

if [[ $$exit_code -ne 0 ]]; then
    echo ""
    echo "Some files are not properly formatted."
    echo "Run 'bazel run //:format' to fix all files."
    exit 1
fi

echo "All Bazel files are properly formatted"
EOF

chmod +x $@
""",
    )

    native.sh_test(
        name = name,
        srcs = [test_script],
        **kwargs
    )

def bazel_files_format_test(name, **kwargs):
    """Convenient macro for testing all Bazel files are formatted."""
    buildifier_test(
        name = name,
        **kwargs
    )

def bazel_files_format(name, **kwargs):
    """Convenient macro for formatting all Bazel files."""
    buildifier_format(
        name = name,
        **kwargs
    )
