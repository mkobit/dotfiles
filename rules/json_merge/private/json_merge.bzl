"""Simple JSON merge rule implementation."""

def _json_merge_impl(ctx):
    """Implementation for json_merge rule."""

    output_file = ctx.actions.declare_file(ctx.attr.out)

    args = ctx.actions.args()
    args.add("--output", output_file.path)
    args.add_all([f.path for f in ctx.files.srcs])

    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = ctx.files.srcs,
        outputs = [output_file],
        mnemonic = "JsonMerge",
        progress_message = "Merging JSON files for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

json_merge = rule(
    implementation = _json_merge_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "JSON files to merge (in order of precedence)",
            allow_files = [".json"],
            mandatory = True,
            allow_empty = False,
        ),
        "out": attr.string(
            doc = "Output filename",
            mandatory = True,
        ),
        "_json_merge_tool": attr.label(
            executable = True,
            cfg = "exec",
            default = Label("//rules/json_merge:json_merge_tool"),
        ),
    },
    doc = """Merge multiple JSON files into a single output file.""",
)
