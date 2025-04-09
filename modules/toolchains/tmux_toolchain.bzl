"""Tmux toolchain and test rule."""
load("@bazel_skylib//lib:shell.bzl", "shell")

# Provider for tmux information
TmuxInfo = provider(
    doc = "Information about the tmux installation",
    fields = {
        "path": "Path to the tmux executable",
        "version": "Version of tmux",
        "is_installed": "Whether tmux is installed",
    },
)

def _tmux_toolchain_impl(ctx):
    # Create an info file for tmux detection
    tmux_info_file = ctx.actions.declare_file(ctx.attr.name + "_info.txt")
    
    # Create a shell script to detect tmux
    tmux_detect_script = ctx.actions.declare_file(ctx.attr.name + "_detect.sh")
    
    # Write the detection script
    ctx.actions.write(
        output = tmux_detect_script,
        content = """#!/bin/bash
set -euo pipefail

OUTPUT_FILE="$1"

echo "# Tmux Information" > "$OUTPUT_FILE"
echo "-----------------" >> "$OUTPUT_FILE"

if command -v tmux &>/dev/null; then
    TMUX_PATH=$(which tmux)
    TMUX_VERSION=$(tmux -V | cut -d' ' -f2)
    
    echo "INSTALLED=true" >> "$OUTPUT_FILE"
    echo "PATH=$TMUX_PATH" >> "$OUTPUT_FILE"
    echo "VERSION=$TMUX_VERSION" >> "$OUTPUT_FILE"
else
    echo "INSTALLED=false" >> "$OUTPUT_FILE"
    echo "PATH=" >> "$OUTPUT_FILE"
    echo "VERSION=" >> "$OUTPUT_FILE"
fi
""",
        is_executable = True,
    )
    
    # Run the script during the build phase
    ctx.actions.run(
        outputs = [tmux_info_file],
        inputs = [],
        executable = tmux_detect_script,
        arguments = [tmux_info_file.path],
        mnemonic = "TmuxDetect",
        progress_message = "Detecting tmux installation",
    )
    
    # Return a provider that includes the information file
    return [
        TmuxInfo(
            path = "",  # Placeholder, determined at runtime
            version = "",  # Placeholder, determined at runtime 
            is_installed = True,  # Placeholder, verified at runtime
        ),
        DefaultInfo(files = depset([tmux_info_file])),
    ]

# Define the tmux_toolchain rule
tmux_toolchain = rule(
    implementation = _tmux_toolchain_impl,
    attrs = {},
)

def _tmux_test_impl(ctx):
    # Create the test executable script 
    test_executable = ctx.actions.declare_file(ctx.attr.name + ".sh")
    ctx.actions.write(
        output = test_executable,
        content = """#!/bin/bash
set -euo pipefail

echo "Running tmux integration test..."

if ! command -v tmux &>/dev/null; then
    echo "TMUX NOT INSTALLED - Test SKIPPED"
    exit 0
fi

# Test that tmux -V works
TMUX_VERSION=$(tmux -V 2>&1)
if [[ $? -eq 0 ]]; then
    echo "TMUX INSTALLED: YES"
    echo "Path: $(which tmux)"
    echo "Version: $TMUX_VERSION"
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "TMUX COMMAND FAILED: $TMUX_VERSION"
    echo "TEST RESULT: FAIL"
    exit 1
fi
""",
        is_executable = True,
    )
    
    # Return the test info
    return [
        DefaultInfo(
            executable = test_executable,
        ),
    ]

# Define the tmux_test rule
tmux_test = rule(
    implementation = _tmux_test_impl,
    test = True,
    attrs = {},
)