# -*- Starlark -*-

"""
Public-facing rules for interacting with `chezmoi`.
"""

def _chezmoi_execute_template_impl(ctx):
    """
    Core implementation of the `chezmoi_execute_template` rule.
    Executes a chezmoi template using the chezmoi binary.
    """
    chezmoi_executable = ctx.executable._chezmoi
    src = ctx.file.src
    out = ctx.outputs.out
    data_file = ctx.file.data_file
    data_srcs = depset(ctx.files.data_srcs)
    source_dir_files = depset(ctx.files.srcs)

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
    data_files_list = data_srcs.to_list()

    for f in data_files_list:
        path = f.path
        if ".chezmoidata/" in path:
            # Extract the part from .chezmoidata/ onwards
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
    source_files_list = source_dir_files.to_list()
    for src_file in source_files_list:
        script_lines.append("ln -s \"$(realpath " + src_file.path + ")\" \"$SOURCE_DIR/" + src_file.basename + "\"")

    # Execute chezmoi
    # Note: We execute chezmoi_executable which is passed as a tool to this script
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

    # Write the script to a file
    script_file = ctx.actions.declare_file(ctx.label.name + "_wrapper.sh")
    ctx.actions.write(
        output = script_file,
        content = "\n".join(script_lines),
        is_executable = True,
    )

    # Collect all inputs
    inputs = [src]
    if data_file:
        inputs.append(data_file)
    if data_files_list:
        inputs.extend(data_files_list)
    if source_files_list:
        inputs.extend(source_files_list)

    # Run the script
    ctx.actions.run(
        outputs = [out],
        inputs = inputs,
        tools = [chezmoi_executable],
        executable = script_file,
        progress_message = "Executing chezmoi template: {}".format(out.short_path),
    )

    return [
        DefaultInfo(files = depset([ctx.outputs.out])),
        ChezmoiTemplateInfo(
            out = ctx.outputs.out,
            chezmoi_executable = chezmoi_executable,
        ),
    ]

ChezmoiTemplateInfo = provider(
    fields = {
        "out": "The output file.",
        "chezmoi_executable": "The chezmoi executable file.",
    },
    doc = "Provider for information about a rendered chezmoi template.",
)

# The private rule definition.
_chezmoi_execute_template = rule(
    implementation = _chezmoi_execute_template_impl,
    provides = [DefaultInfo, ChezmoiTemplateInfo],
    attrs = {
        "src": attr.label(
            allow_single_file = True,
            mandatory = True,
            doc = "The source template file to execute.",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "The output file to generate.",
        ),
        "data_file": attr.label(
            allow_single_file = True,
            doc = "A single data file (e.g., .chezmoidata.toml) to use for templating.",
        ),
        "data_srcs": attr.label_list(
            allow_files = True,
            doc = "A list of data files (e.g. .chezmoidata/**/*.toml) to use.",
        ),
        "srcs": attr.label_list(
            allow_files = True,
            doc = "Additional source files needed by the template (e.g., for chezmoi template functions that read files).",
        ),
        "_chezmoi": attr.label(
            default = Label("@multitool//tools/chezmoi"),
            executable = True,
            cfg = "exec",
        ),
    },
)

# The public-facing macro.
def chezmoi_execute_template(name, src, out, srcs = [], data_file = None, data_srcs = [], data_dict = None, tags = [], visibility = None):
    """
    Executes a `chezmoi` template in a hermetic environment.

    Args:
        name: The name of the rule.
        src: The source template file to execute.
        out: The output file to generate.
        srcs: Additional source files needed by the template.
        data_file: An optional data file (e.g., .chezmoidata.toml).
        data_srcs: An optional list of data files.
        data_dict: An optional dictionary of data to use for templating.
        tags: Standard Bazel tags.
        visibility: Standard Bazel visibility.
    """
    if data_file and data_dict:
        fail("Cannot specify both `data_file` and `data_dict`.")
    if data_dict and data_srcs:
        fail("Cannot specify both `data_dict` and `data_srcs` currently.")

    data_target = data_file

    if data_dict:
        # Convert the dictionary to a TOML string
        toml_lines = []
        for k, v in data_dict.items():
            toml_lines.append('{} = "{}"'.format(k, v))

        toml_content = "\\n".join(toml_lines)
        data_file_name = "{}_data.toml".format(name)
        data_gen_rule_name = "{}_data_gen".format(name)

        native.genrule(
            name = data_gen_rule_name,
            outs = [data_file_name],
            cmd = "cat <<EOF > $@\n" + toml_content + "\nEOF",
        )
        data_target = ":" + data_gen_rule_name

    _chezmoi_execute_template(
        name = name,
        src = src,
        out = out,
        srcs = srcs,
        data_file = data_target,
        data_srcs = data_srcs,
        tags = tags,
        visibility = visibility,
    )
