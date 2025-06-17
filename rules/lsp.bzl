"""
Language Server Protocol (LSP) support for dotfiles project.
"""

def _bazel_lsp_impl(ctx):
    """Implementation for bazel_lsp rule."""
    lsp_binary = ctx.file.lsp_binary
    output_dir = ctx.actions.declare_directory("lsp_config")

    # Create LSP configuration script
    config_script = ctx.actions.declare_file("{}_lsp_config.sh".format(ctx.label.name))

    ctx.actions.write(
        output = config_script,
        content = """#!/bin/bash
set -euo pipefail

LSP_DIR="$1"
LSP_BINARY="{lsp_binary}"

# Create .vscode directory if it doesn't exist
mkdir -p "$LSP_DIR/.vscode"

# Create VSCode settings for Bazel LSP
cat > "$LSP_DIR/.vscode/settings.json" << 'EOF'
{{
  "bazel.lsp.command": "{lsp_binary_path}",
  "bazel.lsp.env": {{
    "RUST_LOG": "info"
  }},
  "bazel.buildifierFixOnFormat": true,
  "bazel.enableCodeLens": true,
  "[bazel]": {{
    "editor.defaultFormatter": "BazelBuild.vscode-bazel"
  }},
  "[starlark]": {{
    "editor.defaultFormatter": "BazelBuild.vscode-bazel"
  }}
}}
EOF

echo "LSP configuration created in $LSP_DIR/.vscode/"
echo "LSP binary: $LSP_BINARY"
echo "Make sure the LSP binary is available in your PATH or update the settings.json path."
""".format(
            lsp_binary = lsp_binary.short_path,
            lsp_binary_path = lsp_binary.short_path,
        ),
        is_executable = True,
    )

    # Run the configuration script
    ctx.actions.run(
        outputs = [output_dir],
        inputs = [lsp_binary],
        executable = config_script,
        arguments = [output_dir.path],
        mnemonic = "BazelLspConfig",
        progress_message = "Configuring Bazel LSP",
    )

    return [DefaultInfo(files = depset([output_dir]))]

bazel_lsp = rule(
    implementation = _bazel_lsp_impl,
    attrs = {
        "lsp_binary": attr.label(
            doc = "The Bazel LSP binary to configure",
            allow_single_file = True,
            mandatory = True,
        ),
    },
    doc = "Create LSP configuration for Bazel files",
)

def _lsp_binary_impl(ctx):
    """Implementation for downloading and building LSP binary."""
    output = ctx.actions.declare_file(ctx.label.name)

    # Download or build the LSP binary
    ctx.actions.run_shell(
        outputs = [output],
        command = """
set -euo pipefail

# Try to find bazel-lsp in common locations
LSP_BINARY=""
if command -v bazel-lsp >/dev/null 2>&1; then
    LSP_BINARY=$(command -v bazel-lsp)
elif command -v cameron-martin-bazel-lsp >/dev/null 2>&1; then
    LSP_BINARY=$(command -v cameron-martin-bazel-lsp)
else
    echo "Warning: No Bazel LSP binary found in PATH"
    echo "You can install one from: https://github.com/cameron-martin/bazel-lsp/releases"
    echo "Creating a placeholder binary"
    cat > {output} << 'EOF'
#!/bin/bash
echo "Bazel LSP binary not found. Please install from:"
echo "https://github.com/cameron-martin/bazel-lsp/releases"
exit 1
EOF
    chmod +x {output}
    exit 0
fi

# Copy the found binary
cp "$LSP_BINARY" {output}
chmod +x {output}
echo "Bazel LSP binary configured: $LSP_BINARY"
""".format(output = output.path),
        mnemonic = "LspBinary",
        progress_message = "Setting up LSP binary",
    )

    return [DefaultInfo(files = depset([output]))]

lsp_binary = rule(
    implementation = _lsp_binary_impl,
    doc = "Download or locate Bazel LSP binary",
)

def _lsp_runner_impl(ctx):
    """Implementation for LSP runner that copies config to workspace."""
    lsp_config = ctx.attr.lsp_config
    runner_script = ctx.actions.declare_file(ctx.label.name + "_runner.sh")

    # Get the LSP config directory from the target
    lsp_config_files = lsp_config.files.to_list()
    if not lsp_config_files:
        fail("No LSP config files found")

    lsp_config_dir = lsp_config_files[0]

    ctx.actions.write(
        output = runner_script,
        content = """#!/bin/bash
set -euo pipefail

echo "Setting up LSP configuration..."

# Get the workspace root (where BUILD.bazel is)
WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
if [[ -z "$WORKSPACE_ROOT" ]]; then
    echo "ERROR: This script must be run with 'bazel run'"
    echo "BUILD_WORKSPACE_DIRECTORY is not set"
    exit 1
fi

# Find the LSP config directory in runfiles
RUNFILES_DIR="$0.runfiles"
if [[ -d "$RUNFILES_DIR" ]]; then
    LSP_CONFIG_DIR="$RUNFILES_DIR/_main/{lsp_config_path}"
else
    # Fallback to direct path
    LSP_CONFIG_DIR="{lsp_config_path}"
fi

echo "Looking for LSP config in: $LSP_CONFIG_DIR"

if [[ -d "$LSP_CONFIG_DIR/.vscode" ]]; then
    echo "Copying .vscode configuration to workspace..."
    mkdir -p "$WORKSPACE_ROOT/.vscode"
    cp -r "$LSP_CONFIG_DIR/.vscode/"* "$WORKSPACE_ROOT/.vscode/"
    echo "✅ LSP configuration installed to $WORKSPACE_ROOT/.vscode/"
else
    echo "❌ LSP configuration directory not found: $LSP_CONFIG_DIR"
    echo "Contents of parent directory:"
    ls -la "$(dirname "$LSP_CONFIG_DIR")" 2>/dev/null || echo "Parent directory not found"
    exit 1
fi

echo "LSP setup complete!"
""".format(
            lsp_config_path = lsp_config_dir.short_path,
        ),
        is_executable = True,
    )

    runfiles = ctx.runfiles(files = lsp_config_files)

    return [DefaultInfo(
        executable = runner_script,
        runfiles = runfiles,
    )]

lsp_runner = rule(
    implementation = _lsp_runner_impl,
    executable = True,
    attrs = {
        "lsp_config": attr.label(
            doc = "The LSP configuration target",
            mandatory = True,
        ),
    },
    doc = "Executable wrapper that installs LSP configuration to workspace",
)

def setup_bazel_lsp(name = "bazel_lsp_setup"):
    """Macro to set up Bazel LSP configuration.

    This creates:
    1. A target to locate/download the LSP binary
    2. A target to configure LSP for the project
    3. An executable target to install the configuration

    Args:
        name: Base name for the targets
    """

    # Create LSP binary target
    lsp_binary(
        name = "{}_binary".format(name),
    )

    # Create LSP configuration target
    bazel_lsp(
        name = "{}_config".format(name),
        lsp_binary = ":{}_binary".format(name),
    )

    # Create executable runner
    lsp_runner(
        name = name,
        lsp_config = ":{}_config".format(name),
    )

def _compile_commands_impl(ctx):
    """Generate compile_commands.json for better IDE support."""
    output = ctx.actions.declare_file("compile_commands.json")

    ctx.actions.run_shell(
        outputs = [output],
        command = """
set -euo pipefail

# Generate a basic compile_commands.json for Bazel projects
cat > {output} << 'EOF'
[
  {{
    "directory": "{workspace}",
    "file": "BUILD.bazel",
    "command": "bazel build //..."
  }}
]
EOF

echo "Generated compile_commands.json"
""".format(
            output = output.path,
            workspace = ctx.workspace_name,
        ),
        mnemonic = "CompileCommands",
        progress_message = "Generating compile_commands.json",
    )

    return [DefaultInfo(files = depset([output]))]

compile_commands = rule(
    implementation = _compile_commands_impl,
    doc = "Generate compile_commands.json for IDE support",
)

def _compile_commands_runner_impl(ctx):
    """Implementation for compile_commands runner that copies file to workspace."""
    compile_commands_file = ctx.file.compile_commands
    runner_script = ctx.actions.declare_file(ctx.label.name + "_runner.sh")

    ctx.actions.write(
        output = runner_script,
        content = """#!/bin/bash
set -euo pipefail

echo "Setting up compile_commands.json..."

# Get the workspace root (where BUILD.bazel is)
WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
if [[ -z "$WORKSPACE_ROOT" ]]; then
    echo "ERROR: This script must be run with 'bazel run'"
    echo "BUILD_WORKSPACE_DIRECTORY is not set"
    exit 1
fi

# Find the compile_commands.json file in runfiles
RUNFILES_DIR="$0.runfiles"
if [[ -d "$RUNFILES_DIR" ]]; then
    COMPILE_COMMANDS_FILE="$RUNFILES_DIR/_main/{compile_commands_path}"
else
    # Fallback to direct path
    COMPILE_COMMANDS_FILE="{compile_commands_path}"
fi

echo "Looking for compile_commands.json at: $COMPILE_COMMANDS_FILE"

if [[ -f "$COMPILE_COMMANDS_FILE" ]]; then
    echo "Copying compile_commands.json to workspace..."
    cp "$COMPILE_COMMANDS_FILE" "$WORKSPACE_ROOT/compile_commands.json"
    echo "✅ compile_commands.json installed to $WORKSPACE_ROOT/"
else
    echo "❌ compile_commands.json not found: $COMPILE_COMMANDS_FILE"
    echo "Contents of parent directory:"
    ls -la "$(dirname "$COMPILE_COMMANDS_FILE")" 2>/dev/null || echo "Parent directory not found"
    exit 1
fi

echo "compile_commands.json setup complete!"
""".format(
            compile_commands_path = compile_commands_file.short_path,
        ),
        is_executable = True,
    )

    runfiles = ctx.runfiles(files = [compile_commands_file])

    return [DefaultInfo(
        executable = runner_script,
        runfiles = runfiles,
    )]

compile_commands_runner = rule(
    implementation = _compile_commands_runner_impl,
    executable = True,
    attrs = {
        "compile_commands": attr.label(
            doc = "The compile_commands.json file",
            allow_single_file = True,
            mandatory = True,
        ),
    },
    doc = "Executable wrapper that installs compile_commands.json to workspace",
)
