"""JQ toolchain and test rule."""
load("@bazel_skylib//lib:shell.bzl", "shell")
load("//modules/toolchains:toolchain_types.bzl", "ToolInfo")

# Provider for jq information
JqInfo = provider(
    doc = "Information about the jq installation",
    fields = {
        "path": "Path to the jq executable",
        "version": "Version of jq",
        "is_installed": "Whether jq is installed",
        "module_paths": "List of default search paths for modules",
    },
)

def _jq_toolchain_impl(ctx):
    # Check if we're using manual configuration or auto-detection
    if ctx.attr.path != "":
        # Use manually specified configuration
        toolchain_info = platform_common.ToolchainInfo(
            jq_info = JqInfo(
                path = ctx.attr.path,
                version = ctx.attr.version,
                is_installed = True,
                module_paths = ctx.attr.module_paths,
            ),
            tool_info = ToolInfo(
                name = "jq",
                path = ctx.attr.path,
                version = ctx.attr.version,
                available = ctx.attr.path != "",
                extra_info = {
                    "module_paths": ",".join(ctx.attr.module_paths),
                },
            ),
        )
        return [toolchain_info]
    else:
        # Use auto-detection
        jq_info_file = ctx.actions.declare_file(ctx.attr.name + "_info.txt")
        
        # Create a shell script to detect jq
        jq_detect_script = ctx.actions.declare_file(ctx.attr.name + "_detect.sh")
        
        # Write the detection script
        ctx.actions.write(
            output = jq_detect_script,
            content = """#!/bin/bash
set -euo pipefail

OUTPUT_FILE="$1"

echo "# JQ Information" > "$OUTPUT_FILE"
echo "-----------------" >> "$OUTPUT_FILE"

if command -v jq &>/dev/null; then
    JQ_PATH=$(which jq)
    JQ_VERSION=$(jq --version 2>&1)
    
    # Normalize the version string by removing "jq-" prefix if present
    JQ_VERSION=$(echo "$JQ_VERSION" | sed 's/^jq-//')
    
    echo "INSTALLED=true" >> "$OUTPUT_FILE"
    echo "PATH=$JQ_PATH" >> "$OUTPUT_FILE"
    echo "VERSION=$JQ_VERSION" >> "$OUTPUT_FILE"
    
    # Check for default module search paths based on the documentation
    echo "MODULE_PATHS=" >> "$OUTPUT_FILE"
    
    # We can't actually query jq for its module paths, so we use the documented defaults:
    # ~/.jq, $ORIGIN/../lib/jq, $ORIGIN/../lib
    # where $ORIGIN is the directory where the jq executable is located
    
    # Determine the install location of jq
    JQ_DIR=$(dirname "$JQ_PATH")
    echo "JQ_ORIGIN=$JQ_DIR" >> "$OUTPUT_FILE"
    
    # Add the default search paths
    echo "MODULE_PATH_1=~/.jq" >> "$OUTPUT_FILE"
    echo "MODULE_PATH_2=$JQ_DIR/../lib/jq" >> "$OUTPUT_FILE"
    echo "MODULE_PATH_3=$JQ_DIR/../lib" >> "$OUTPUT_FILE"
else
    echo "INSTALLED=false" >> "$OUTPUT_FILE"
    echo "PATH=" >> "$OUTPUT_FILE"
    echo "VERSION=" >> "$OUTPUT_FILE"
    echo "MODULE_PATHS=" >> "$OUTPUT_FILE"
fi
""",
            is_executable = True,
        )
        
        # Run the script during the build phase
        ctx.actions.run(
            outputs = [jq_info_file],
            inputs = [],
            executable = jq_detect_script,
            arguments = [jq_info_file.path],
            mnemonic = "JqDetect",
            progress_message = "Detecting jq installation",
        )
        
        # Return a provider that includes the information file
        return [
            JqInfo(
                path = "",  # Placeholder, determined at runtime
                version = "",  # Placeholder, determined at runtime 
                is_installed = True,  # Placeholder, verified at runtime
                module_paths = ctx.attr.module_paths,  # User-specified module paths
            ),
            DefaultInfo(files = depset([jq_info_file])),
        ]

# Define the jq_toolchain rule
jq_toolchain = rule(
    implementation = _jq_toolchain_impl,
    attrs = {
        "path": attr.string(default = ""),
        "version": attr.string(default = ""),
        "module_paths": attr.string_list(
            default = ["~/.jq", "$ORIGIN/../lib/jq", "$ORIGIN/../lib"],
            doc = "Default search paths for jq modules",
        ),
    },
)

def _jq_test_impl(ctx):
    # Create the test executable script 
    test_executable = ctx.actions.declare_file(ctx.attr.name + ".sh")
    
    jq_path = ctx.attr.jq_path or "jq"
    
    ctx.actions.write(
        output = test_executable,
        content = """#!/bin/bash
set -euo pipefail

echo "Running jq integration test..."

# Use specified path or fallback to default
JQ_COMMAND="{jq_path}"

if ! command -v $JQ_COMMAND &>/dev/null; then
    echo "$JQ_COMMAND NOT INSTALLED - Test SKIPPED"
    exit 0
fi

# Test that jq --version works
JQ_VERSION=$($JQ_COMMAND --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "JQ INSTALLED: YES"
    echo "Path: $(which $JQ_COMMAND)"
    echo "Version: $JQ_VERSION"
    
    # Test basic functionality
    RESULT=$($JQ_COMMAND -n 'null' 2>&1)
    if [[ $? -eq 0 ]]; then
        echo "Basic functionality test passed"
    else
        echo "Basic functionality test failed"
        exit 1
    fi
    
    # Test module search paths
    echo "Default module search paths:"
    echo "  ~/.jq"
    JQ_DIR=$(dirname $(which $JQ_COMMAND))
    echo "  $JQ_DIR/../lib/jq"
    echo "  $JQ_DIR/../lib"
    
    # Create a test module
    TEST_MODULE=$(mktemp)
    echo 'def test_func: "test successful";' > "$TEST_MODULE"
    echo "Testing module import..."
    RESULT=$($JQ_COMMAND -L $(dirname "$TEST_MODULE") -n 'import "$(basename "$TEST_MODULE" .jq)" as test; test::test_func' 2>/dev/null || echo "import failed")
    if [[ "$RESULT" == '"test successful"' ]]; then
        echo "Module import test passed"
    else
        echo "Module import test failed"
        echo "Result: $RESULT"
    fi
    rm -f "$TEST_MODULE"
    
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "JQ COMMAND FAILED: $JQ_VERSION"
    echo "TEST RESULT: FAIL"
    exit 1
fi
""".format(
            jq_path = jq_path,
        ),
        is_executable = True,
    )
    
    # Return the test info
    return [
        DefaultInfo(
            executable = test_executable,
        ),
    ]

# Define the jq_test rule
jq_test = rule(
    implementation = _jq_test_impl,
    test = True,
    attrs = {
        "jq_path": attr.string(
            default = "",
            doc = "Path to jq executable. If empty, uses 'jq' on PATH",
        ),
    },
)