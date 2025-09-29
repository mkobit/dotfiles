# -*- Starlark -*-

"""Private `chezmoi` toolchain definition."""

def _execute_template_action(
        ctx,
        src,
        out,
        data,
        source_dir_files):
    """
    Creates a `run_shell` action to execute a chezmoi template.
    """
    chezmoi_info = ctx.toolchains["@//tools/chezmoi:toolchain_type"]
    chezmoi_executable = chezmoi_info.chezmoi_executable

    script_lines = [
        "#!/bin/bash",
        "set -euo pipefail",

        # --- Create a self-contained, writable environment for chezmoi ---
        "export HOME=$(mktemp -d)",
        "WORK_DIR=$(mktemp -d)",

        # Copy all source files into the working directory.
        # The -L flag is important to dereference symlinks from the Bazel sandbox.
        "cp -LR " + "$(dirname " + source_dir_files.to_list()[0].path + ")/." + " $WORK_DIR",

        # Copy the template to be executed into the working directory.
        "cp -L " + src.path + " $WORK_DIR/" + src.basename,

        # If a data file is provided, copy it to the location where chezmoi expects it.
    ]
    if data:
        script_lines.append("cp -L " + data.path + " $WORK_DIR/.chezmoidata.toml")

    # --- Execute chezmoi ---
    # The path to the template inside the new, writable source directory.
    template_in_work_dir = "$WORK_DIR/" + src.basename

    chezmoi_cmd_parts = [
        # Use the absolute path to the executable, as we're changing directory.
        "$(pwd)/" + chezmoi_executable.path,
        "execute-template",
        "--source $WORK_DIR", # Use the CLI flag instead of env var
        "--file",
        # Use the absolute path for the output file.
        "--output $(pwd)/" + out.path,
        template_in_work_dir,
    ]
    script_lines.append(" ".join(chezmoi_cmd_parts))

    direct_inputs = [src, chezmoi_executable]
    if data:
        direct_inputs.append(data)

    inputs = depset(
        direct = direct_inputs,
        transitive = [source_dir_files],
    )

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