"""JSON merge and patch rule implementations."""

def _json_merge_impl(ctx):
    """Implementation for json_merge rule."""

    output_file = ctx.actions.declare_file(ctx.attr.out)

    args = ctx.actions.args()
    args.add("--merge")
    args.add("--base", ctx.file.base.path)
    args.add("--src", ctx.file.src.path)
    args.add("--output", output_file.path)

    inputs = [ctx.file.base, ctx.file.src]

    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
        mnemonic = "JsonMerge",
        progress_message = "Merging JSON files for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

def _json_patch_impl(ctx):
    """Implementation for json_patch rule."""

    output_file = ctx.actions.declare_file(ctx.attr.out)

    args = ctx.actions.args()
    args.add("--base", ctx.file.base.path)
    args.add("--output", output_file.path)
    args.add_all([f.path for f in ctx.files.patches])

    inputs = [ctx.file.base] + ctx.files.patches

    ctx.actions.run(
        executable = ctx.executable._json_patch_tool,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
        mnemonic = "JsonPatch",
        progress_message = "Applying JSON patches for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

json_patch = rule(
    implementation = _json_patch_impl,
    attrs = {
        "base": attr.label(
            doc = "Base JSON file to patch",
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "patches": attr.label_list(
            doc = "JSON patch files to apply (in order)",
            allow_files = [".json", ".jsonpatch"],
            mandatory = False,
            default = [],
        ),
        "out": attr.string(
            doc = "Output filename",
            mandatory = True,
        ),
        "_json_patch_tool": attr.label(
            executable = True,
            cfg = "exec",
            default = Label("//rules/json_merge:json_merge_tool"),
        ),
    },
    doc = """Apply JSON patches to a base JSON file.""",
)

json_merge = rule(
    implementation = _json_merge_impl,
    attrs = {
        "base": attr.label(
            doc = "Base JSON file to merge with",
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "src": attr.label(
            doc = "JSON file to merge into base",
            allow_single_file = [".json"],
            mandatory = True,
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
    doc = """Deep merge two JSON files.""",
)
