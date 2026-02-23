
def _rulesync_generate_impl(ctx):
    out_dir = ctx.actions.declare_directory(ctx.attr.out)
    rulesync_tool = ctx.executable._rulesync

    inputs = []
    inputs.extend(ctx.files.srcs)
    if ctx.file.config:
        inputs.append(ctx.file.config)

    commands = [
        "set -euo pipefail",
        # Create a workspace directory to isolate execution
        "mkdir -p workspace/.rulesync",
    ]

    # Link config
    if ctx.file.config:
        commands.append("ln -s \"$PWD/{}\" workspace/rulesync.jsonc".format(ctx.file.config.path))
    else:
        commands.append("echo '{\"targets\": [], \"baseDirs\": [\".\"]}' > workspace/rulesync.jsonc")

    # Link sources
    for f in ctx.files.srcs:
        rel_path = f.short_path
        if ctx.attr.strip_prefix:
            if rel_path.startswith(ctx.attr.strip_prefix):
                rel_path = rel_path[len(ctx.attr.strip_prefix):]
                if rel_path.startswith("/"):
                    rel_path = rel_path[1:]

        dest_path = "workspace/.rulesync/" + rel_path
        commands.append("mkdir -p \"$(dirname \"{}\")\"".format(dest_path))
        commands.append("ln -s \"$PWD/{}\" \"{}\"".format(f.path, dest_path))

    # Run rulesync inside workspace
    target_args = ",".join(ctx.attr.targets)
    # We cd into workspace to run rulesync
    # Note: rulesync tool path is relative to sandbox root (or absolute).
    # rulesync_tool.path is relative to execroot.
    # $PWD is execroot.
    # So we can access tool via "$PWD/{rulesync_tool.path}"

    commands.append("cd workspace")
    commands.append("\"$PWD/../{}\" generate --targets \"{}\"".format(rulesync_tool.path, target_args))

    # Prepare output directory (relative to execroot, so ../out_dir.path from workspace)
    commands.append("mkdir -p \"$PWD/../{}\"".format(out_dir.path))

    # Move generated content to output
    # Exclude .rulesync and rulesync.jsonc
    # We use find . inside workspace.
    # The output path is relative to execroot.
    # We use $PWD/../out_dir.path to refer to it absolute (or relative from workspace).
    # Since we are in workspace, ../out_dir.path works if out_dir is in execroot.

    commands.append("find . -maxdepth 1 -not -path '.' -not -path './.rulesync' -not -path './rulesync.jsonc' -exec cp -r {{}} \"$PWD/../{}/\" \\;".format(out_dir.path))

    ctx.actions.run_shell(
        inputs = inputs,
        outputs = [out_dir],
        tools = [rulesync_tool],
        command = "\n".join(commands),
        mnemonic = "RulesyncGenerate",
        progress_message = "Generating rulesync configuration for targets: {}".format(", ".join(ctx.attr.targets)),
    )

    return [DefaultInfo(files = depset([out_dir]))]

rulesync_generate = rule(
    implementation = _rulesync_generate_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True, doc = "Source rule files"),
        "config": attr.label(allow_single_file = True, doc = "Optional rulesync.jsonc configuration file"),
        "targets": attr.string_list(mandatory = True, doc = "List of targets to generate for"),
        "out": attr.string(mandatory = True, doc = "Name of the output directory"),
        "strip_prefix": attr.string(doc = "Prefix to strip from source file paths"),
        "_rulesync": attr.label(
            default = "@multitool//tools/rulesync",
            executable = True,
            cfg = "exec",
        ),
    },
)
