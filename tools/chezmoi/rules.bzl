# -*- Starlark -*-

"""
Public-facing rules for interacting with `chezmoi`.
"""

def _chezmoi_execute_template_impl(ctx):
    """
    Core implementation of the `chezmoi_execute_template` rule.
    This rule now delegates the action creation to the toolchain.
    """
    chezmoi_info = ctx.toolchains["@//tools/chezmoi:toolchain_type"]

    # Call the high-level API provided by the toolchain
    chezmoi_info.execute_template(
        ctx = ctx,  # Pass our context to the toolchain helper
        src = ctx.file.src,
        out = ctx.outputs.out,
        data_file = ctx.file.data_file,
        data_srcs = depset(ctx.files.data_srcs),
        source_dir_files = depset(ctx.files.srcs),
    )

    return [
        DefaultInfo(files = depset([ctx.outputs.out])),
        ChezmoiTemplateInfo(
            out = ctx.outputs.out,
            chezmoi_executable = chezmoi_info.chezmoi_executable,
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
    },
    toolchains = ["@//tools/chezmoi:toolchain_type"],
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
