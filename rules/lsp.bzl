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

def setup_bazel_lsp(name = "bazel_lsp_setup"):
    """Macro to set up Bazel LSP configuration.

    This creates:
    1. A target to locate/download the LSP binary
    2. A target to configure LSP for the project

    Args:
        name: Base name for the targets
    """

    # Create LSP binary target
    lsp_binary(
        name = "{}_binary".format(name),
    )

    # Create LSP configuration target
    bazel_lsp(
        name = name,
        lsp_binary = ":{}_binary".format(name),
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
