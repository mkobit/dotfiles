"""
Simplified Language Server Protocol (LSP) support for dotfiles project.

Replaces 330+ lines of complex runfiles/runners with simple file generation.
"""

def _simple_vscode_settings_impl(ctx):
    """Generate simple VSCode settings for Bazel LSP."""
    output = ctx.actions.declare_file("settings.json")

    ctx.actions.write(
        output = output,
        content = """{
  "bazel.lsp.command": "bazel-lsp",
  "bazel.lsp.env": {
    "RUST_LOG": "info"
  },
  "bazel.buildifierFixOnFormat": true,
  "bazel.enableCodeLens": true,
  "[bazel]": {
    "editor.defaultFormatter": "BazelBuild.vscode-bazel"
  },
  "[starlark]": {
    "editor.defaultFormatter": "BazelBuild.vscode-bazel"
  }
}""",
    )

    return [DefaultInfo(files = depset([output]))]

simple_vscode_settings = rule(
    implementation = _simple_vscode_settings_impl,
    doc = "Generate VSCode settings.json for Bazel LSP",
)

def _simple_compile_commands_impl(ctx):
    """Generate basic compile_commands.json for IDE support."""
    output = ctx.actions.declare_file("compile_commands.json")

    ctx.actions.write(
        output = output,
        content = """[
  {
    "directory": "%s",
    "file": "BUILD.bazel", 
    "command": "bazel build //..."
  }
]""" % ctx.workspace_name,
    )

    return [DefaultInfo(files = depset([output]))]

simple_compile_commands = rule(
    implementation = _simple_compile_commands_impl,
    doc = "Generate basic compile_commands.json for IDE support",
)

def setup_simple_lsp(name = "lsp_setup"):
    """Simplified macro to set up basic LSP support.

    Creates VSCode settings and compile_commands files that can be
    copied to the workspace root manually if needed.

    Args:
        name: Base name for the targets
    """

    simple_vscode_settings(
        name = name + "_vscode_settings",
    )

    simple_compile_commands(
        name = name + "_compile_commands",
    )
