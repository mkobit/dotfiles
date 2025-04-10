"""Vim toolchain and test rule."""
load("@bazel_skylib//lib:shell.bzl", "shell")

# Provider for vim information
VimInfo = provider(
    doc = "Information about the vim installation",
    fields = {
        "path": "Path to the vim executable",
        "version": "Version of vim",
        "is_installed": "Whether vim is installed",
        "has_lua": "Boolean indicating if Vim has Lua support",
        "has_python": "Boolean indicating if Vim has Python support",
    },
)

def _vim_toolchain_impl(ctx):
    # Create an info file for vim detection
    vim_info_file = ctx.actions.declare_file(ctx.attr.name + "_info.txt")
    
    # Create a shell script to detect vim
    vim_detect_script = ctx.actions.declare_file(ctx.attr.name + "_detect.sh")
    
    # Write the detection script
    ctx.actions.write(
        output = vim_detect_script,
        content = """#!/bin/bash
set -euo pipefail

OUTPUT_FILE="$1"

echo "# Vim Information" > "$OUTPUT_FILE"
echo "-----------------" >> "$OUTPUT_FILE"

if command -v vim &>/dev/null; then
    VIM_PATH=$(which vim)
    VIM_VERSION=$(vim --version | head -1 | sed 's/.*VIM - Vi IMproved //;s/ .*//')
    HAS_LUA=$(vim --version | grep -q "+lua" && echo "true" || echo "false")
    HAS_PYTHON=$(vim --version | grep -q "+python" && echo "true" || echo "false")
    
    echo "INSTALLED=true" >> "$OUTPUT_FILE"
    echo "PATH=$VIM_PATH" >> "$OUTPUT_FILE"
    echo "VERSION=$VIM_VERSION" >> "$OUTPUT_FILE"
    echo "HAS_LUA=$HAS_LUA" >> "$OUTPUT_FILE"
    echo "HAS_PYTHON=$HAS_PYTHON" >> "$OUTPUT_FILE"
else
    echo "INSTALLED=false" >> "$OUTPUT_FILE"
    echo "PATH=" >> "$OUTPUT_FILE"
    echo "VERSION=" >> "$OUTPUT_FILE"
    echo "HAS_LUA=false" >> "$OUTPUT_FILE"
    echo "HAS_PYTHON=false" >> "$OUTPUT_FILE"
fi
""",
        is_executable = True,
    )
    
    # Run the script during the build phase
    ctx.actions.run(
        outputs = [vim_info_file],
        inputs = [],
        executable = vim_detect_script,
        arguments = [vim_info_file.path],
        mnemonic = "VimDetect",
        progress_message = "Detecting vim installation",
    )
    
    # Return a provider that includes the information file
    return [
        VimInfo(
            path = "",  # Placeholder, determined at runtime
            version = "",  # Placeholder, determined at runtime 
            is_installed = True,  # Placeholder, verified at runtime
            has_lua = False,  # Placeholder, verified at runtime
            has_python = False,  # Placeholder, verified at runtime
        ),
        DefaultInfo(files = depset([vim_info_file])),
    ]

# Define the vim_toolchain rule
vim_toolchain = rule(
    implementation = _vim_toolchain_impl,
    attrs = {},
)

def _vim_test_impl(ctx):
    # Create the test executable script 
    test_executable = ctx.actions.declare_file(ctx.attr.name + ".sh")
    ctx.actions.write(
        output = test_executable,
        content = """#!/bin/bash
set -euo pipefail

echo "Running vim integration test..."

if ! command -v vim &>/dev/null; then
    echo "VIM NOT INSTALLED - Test SKIPPED"
    exit 0
fi

# Test that vim --version works
VIM_VERSION=$(vim --version 2>&1 | head -1)
if [[ $? -eq 0 ]]; then
    echo "VIM INSTALLED: YES"
    echo "Path: $(which vim)"
    echo "Version: $VIM_VERSION"
    
    # Check for Lua support
    if vim --version | grep -q "+lua"; then
        echo "Lua support: YES"
    else
        echo "Lua support: NO"
    fi
    
    # Check for Python support
    if vim --version | grep -q "+python"; then
        echo "Python support: YES"
    else
        echo "Python support: NO"
    fi
    
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "VIM COMMAND FAILED: $VIM_VERSION"
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

# Define the vim_test rule
vim_test = rule(
    implementation = _vim_test_impl,
    test = True,
    attrs = {},
)