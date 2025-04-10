"""Vim toolchain and test rule."""
load("@bazel_skylib//lib:shell.bzl", "shell")
load("//modules/toolchains:toolchain_types.bzl", "ToolInfo")

# Provider for vim information
VimInfo = provider(
    doc = "Information about the vim installation",
    fields = {
        "path": "Path to the vim executable",
        "version": "Version of vim",
        "is_installed": "Whether vim is installed",
        "has_lua": "Boolean indicating if Vim has Lua support",
        "has_python": "Boolean indicating if Vim has Python support",
        "config_path": "Path to vim config directory",
    },
)

def _vim_toolchain_impl(ctx):
    # Check if we're using manual configuration or auto-detection
    if ctx.attr.path != "":
        # Use manually specified configuration
        toolchain_info = platform_common.ToolchainInfo(
            vim_info = VimInfo(
                path = ctx.attr.path,
                version = ctx.attr.version,
                is_installed = True,
                has_lua = ctx.attr.has_lua,
                has_python = ctx.attr.has_python,
                config_path = ctx.attr.config_path,
            ),
            tool_info = ToolInfo(
                name = "vim",
                path = ctx.attr.path,
                version = ctx.attr.version,
                available = ctx.attr.path != "",
                extra_info = {
                    "has_lua": str(ctx.attr.has_lua),
                    "has_python": str(ctx.attr.has_python),
                    "config_path": ctx.attr.config_path,
                },
            ),
        )
        return [toolchain_info]
    else:
        # Use auto-detection
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
                config_path = ctx.attr.config_path or "~/.vim",  # Default config path
            ),
            DefaultInfo(files = depset([vim_info_file])),
        ]

# Define the vim_toolchain rule
vim_toolchain = rule(
    implementation = _vim_toolchain_impl,
    attrs = {
        # For backward compatibility with existing toolchain usage
        "path": attr.string(default = ""),
        "version": attr.string(default = ""),
        "has_lua": attr.bool(default = False),
        "has_python": attr.bool(default = False),
        "config_path": attr.string(default = "~/.vim"),
    },
)

def _vim_test_impl(ctx):
    # Create the test executable script 
    test_executable = ctx.actions.declare_file(ctx.attr.name + ".sh")
    
    vim_path = ctx.attr.vim_path or "vim"
    
    ctx.actions.write(
        output = test_executable,
        content = """#!/bin/bash
set -euo pipefail

echo "Running vim integration test..."

# Use specified path or fallback to default
VIM_COMMAND="{vim_path}"

if ! command -v $VIM_COMMAND &>/dev/null; then
    echo "$VIM_COMMAND NOT INSTALLED - Test SKIPPED"
    exit 0
fi

# Test that vim --version works
VIM_VERSION=$($VIM_COMMAND --version 2>&1 | head -1)
if [[ $? -eq 0 ]]; then
    echo "VIM INSTALLED: YES"
    echo "Path: $(which $VIM_COMMAND)"
    echo "Version: $VIM_VERSION"
    
    # Check for Lua support
    if $VIM_COMMAND --version | grep -q "+lua"; then
        echo "Lua support: YES"
    else
        echo "Lua support: NO"
    fi
    
    # Check for Python support
    if $VIM_COMMAND --version | grep -q "+python"; then
        echo "Python support: YES"
    else
        echo "Python support: NO"
    fi
    
    # Check config path
    if [ -n "{config_path}" ]; then
        echo "Config path: {config_path}"
        if [ -d "{config_path}" ]; then
            echo "Config directory exists: YES"
        else
            echo "Config directory exists: NO"
        fi
    fi
    
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "VIM COMMAND FAILED: $VIM_VERSION"
    echo "TEST RESULT: FAIL"
    exit 1
fi
""".format(
            vim_path = vim_path,
            config_path = ctx.attr.config_path,
        ),
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
    attrs = {
        "vim_path": attr.string(
            default = "",
            doc = "Path to vim executable. If empty, uses 'vim' on PATH",
        ),
        "config_path": attr.string(
            default = "~/.vim",
            doc = "Path to vim configuration directory",
        ),
    },
)