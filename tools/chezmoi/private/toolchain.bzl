# -*- Starlark -*-

"""Private `chezmoi` toolchain definition."""

def _execute_template_action(
        ctx,
        src,
        out,
        data_file,
        data_srcs,
        source_dir_files):
    """
    Creates actions to execute a chezmoi template.
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
        "# Symlink template file",
        "ln -s \"$(realpath " + src.path + ")\" \"$SOURCE_DIR/" + src.basename + "\"",
    ]

    # Handle single data file (legacy/simple mode)
    if data_file:
        script_lines.append("ln -s \"$(realpath " + data_file.path + ")\" \"$SOURCE_DIR/.chezmoidata.toml\"")

    # Handle data sources (list of files)
    # We attempt to preserve the structure if it matches standard chezmoi patterns
    data_files_list = data_srcs.to_list() if data_srcs else []

    # We pass the list of data files to the script to handle logic there if strict path mapping is needed.
    # But simpler to just loop in starlark and generate commands if the list is not huge.
    for f in data_files_list:
        # Heuristic: place .chezmoidata* files in the root or .chezmoidata/ subdir of SOURCE_DIR
        # If the file path contains .chezmoidata, we respect that structure.
        # e.g. src/.chezmoidata/foo.toml -> $SOURCE_DIR/.chezmoidata/foo.toml

        # In bash, we can do some detection, but hardcoding the paths here based on Bazel's info is better.
        # We assume the user provides files that should be in the source root.
        # If they are in a subdir in the source, we assume that subdir is meaningful.

        # Logic:
        # 1. If filename is .chezmoidata.toml, put at root.
        # 2. If path contains .chezmoidata/, ensure .chezmoidata dir exists and link there.

        path = f.path
        if ".chezmoidata/" in path:
            # Extract the part from .chezmoidata/ onwards
            # e.g. src/.chezmoidata/foo.toml -> .chezmoidata/foo.toml
            target_rel = path[path.find(".chezmoidata/"):]
            target_dir = "$SOURCE_DIR/" + target_rel.rsplit("/", 1)[0]
            script_lines.append("mkdir -p \"" + target_dir + "\"")
            script_lines.append("ln -s \"$(realpath " + path + ")\" \"$SOURCE_DIR/" + target_rel + "\"")
        elif f.basename == ".chezmoidata.toml":
            script_lines.append("ln -s \"$(realpath " + path + ")\" \"$SOURCE_DIR/.chezmoidata.toml\"")
        else:
            # Fallback: link to root
            script_lines.append("ln -s \"$(realpath " + path + ")\" \"$SOURCE_DIR/" + f.basename + "\"")

    # Copy any additional source files
    source_files_list = source_dir_files.to_list() if source_dir_files else []
    for src_file in source_files_list:
        script_lines.append("ln -s \"$(realpath " + src_file.path + ")\" \"$SOURCE_DIR/" + src_file.basename + "\"")

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
    if data_file:
        inputs.append(data_file)
    if data_files_list:
        inputs.extend(data_files_list)
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
