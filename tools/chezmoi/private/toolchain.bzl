# -*- Starlark -*-

"""Private `chezmoi` toolchain definition."""

def _execute_template_action(
        ctx,
        src,
        out,
        data,
        source_dir_files):
    """
    Creates actions to execute a chezmoi template.

    This implementation creates a hermetic temporary directory with all
    necessary files and runs chezmoi execute-template against it.
    """
    chezmoi_info = ctx.toolchains["@//tools/chezmoi:toolchain_type"]
    chezmoi_executable = chezmoi_info.chezmoi_executable

    # Build script to create source directory and execute chezmoi
    script_lines = [
        "#!/bin/bash",
        "set -euo pipefail",
        "",
        "# Create local directories for hermetic execution",
        "CHEZMOI_HOME=\"$PWD/chezmoi_home\"",
        "SOURCE_DIR=\"$PWD/chezmoi_source\"",
        "mkdir -p \"$CHEZMOI_HOME\"",
        "mkdir -p \"$SOURCE_DIR\"",
        "",
        "# Set HOME to our fake home directory",
        "export HOME=\"$CHEZMOI_HOME\"",
        "",
        "# Copy template file",
        "cp -L \"" + src.path + "\" \"$SOURCE_DIR/" + src.basename + "\"",
    ]

    # Copy data file if provided
    if data:
        script_lines.append("cp -L \"" + data.path + "\" \"$SOURCE_DIR/.chezmoidata.toml\"")

    # Copy any additional source files
    source_files_list = source_dir_files.to_list() if source_dir_files else []
    for src_file in source_files_list:
        script_lines.append("cp -L \"" + src_file.path + "\" \"$SOURCE_DIR/" + src_file.basename + "\"")

    # Execute chezmoi
    script_lines.extend([
        "",
        "# Execute chezmoi template",
        " ".join([
            "\"" + chezmoi_executable.path + "\"",
            "execute-template",
            "--source \"$SOURCE_DIR\"",
            "--file",
            "--output \"" + out.path + "\"",
            "\"$SOURCE_DIR/" + src.basename + "\"",
        ]),
    ])

    # Collect all inputs
    inputs = [src, chezmoi_executable]
    if data:
        inputs.append(data)
    if source_files_list:
        inputs.extend(source_files_list)

    ctx.actions.run_shell(
        outputs = [out],
        inputs = inputs,
        command = "\n".join(script_lines),
        progress_message = "Executing chezmoi template: {}".format(out.short_path),
    )

def _chezmoi_toolchain_impl(ctx):
    """
    Implementation of the `chezmoi` toolchain rule.
    """
    toolchain_info = platform_common.ToolchainInfo(
        chezmoi_executable = ctx.executable.chezmoi,
        execute_template = _execute_template_action,
    )
    return [toolchain_info]

chezmoi_toolchain = rule(
    implementation = _chezmoi_toolchain_impl,
    attrs = {
        "chezmoi": attr.label(
            allow_single_file = True,
            cfg = "exec",
            executable = True,
            mandatory = True,
        ),
    },
)
