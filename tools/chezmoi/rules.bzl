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
        data = ctx.file.data,
        source_dir_files = depset(ctx.files._source_dir),  # Convert file list to depset
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

# The private rule definition. The attributes remain the same.
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
        "data": attr.label(
            allow_single_file = True,
            doc = "The data file (e.g., .chezmoidata.toml) to use for templating.",
        ),
        "_source_dir": attr.label(
            default = Label("//src:all_files"),
            doc = "Implicit dependency on all files in the chezmoi source directory.",
        ),
    },
    toolchains = ["@//tools/chezmoi:toolchain_type"],
)

# The public-facing macro remains the same.
def chezmoi_execute_template(name, src, out, data_file = None, data_dict = None, tags = [], visibility = None):
    """
    Executes a `chezmoi` template in a hermetic environment.

    Args:
        name: The name of the rule.
        src: The source template file to execute.
        out: The output file to generate.
        data_file: An optional data file (e.g., .chezmoidata.toml) for templating.
        data_dict: An optional dictionary of data to use for templating.
        tags: Standard Bazel tags.
        visibility: Standard Bazel visibility.
    """
    if data_file and data_dict:
        fail("Cannot specify both `data_file` and `data_dict`.")

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
            cmd = "echo -e '" + toml_content + "' > $@",
        )
        data_target = ":" + data_gen_rule_name

    _chezmoi_execute_template(
        name = name,
        src = src,
        out = out,
        data = data_target,
        tags = tags,
        visibility = visibility,
    )