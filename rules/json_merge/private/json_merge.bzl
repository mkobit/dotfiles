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

    inputs = [ctx.file.base]

    # Handle inline patch operations
    if ctx.attr.patch_ops:
        # Create temporary patch file from inline operations
        patch_file = ctx.actions.declare_file(ctx.attr.out + ".patch")

        # patch_ops should be a JSON string containing the patch array
        ctx.actions.write(
            output = patch_file,
            content = ctx.attr.patch_ops,
        )
        args.add("--inline-patch", patch_file.path)
        inputs.append(patch_file)

    # Handle file-based patches
    if ctx.files.patches:
        args.add_all([f.path for f in ctx.files.patches])
        inputs.extend(ctx.files.patches)

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
        "patch_ops": attr.string(
            doc = "Inline JSON patch operations as JSON string",
            mandatory = False,
            default = "",
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

def _json_add_impl(ctx):
    """Implementation for json_add rule."""
    output_file = ctx.actions.declare_file(ctx.attr.out)

    # Create patch operation
    patch_op = '[{"op": "add", "path": "' + ctx.attr.path + '", "value": ' + ctx.attr.value + "}]"
    patch_file = ctx.actions.declare_file(ctx.attr.out + ".patch")
    ctx.actions.write(
        output = patch_file,
        content = patch_op,
    )

    args = ctx.actions.args()
    args.add("--base", ctx.file.base.path)
    args.add("--output", output_file.path)
    args.add("--inline-patch", patch_file.path)

    inputs = [ctx.file.base, patch_file]

    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
        mnemonic = "JsonAdd",
        progress_message = "Adding JSON value for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

def _json_replace_impl(ctx):
    """Implementation for json_replace rule."""
    output_file = ctx.actions.declare_file(ctx.attr.out)

    # Create patch operation
    patch_op = '[{"op": "replace", "path": "' + ctx.attr.path + '", "value": ' + ctx.attr.value + "}]"
    patch_file = ctx.actions.declare_file(ctx.attr.out + ".patch")
    ctx.actions.write(
        output = patch_file,
        content = patch_op,
    )

    args = ctx.actions.args()
    args.add("--base", ctx.file.base.path)
    args.add("--output", output_file.path)
    args.add("--inline-patch", patch_file.path)

    inputs = [ctx.file.base, patch_file]

    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
        mnemonic = "JsonReplace",
        progress_message = "Replacing JSON value for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

def _json_remove_impl(ctx):
    """Implementation for json_remove rule."""
    output_file = ctx.actions.declare_file(ctx.attr.out)

    # Create patch operation
    patch_op = '[{"op": "remove", "path": "' + ctx.attr.path + '"}]'
    patch_file = ctx.actions.declare_file(ctx.attr.out + ".patch")
    ctx.actions.write(
        output = patch_file,
        content = patch_op,
    )

    args = ctx.actions.args()
    args.add("--base", ctx.file.base.path)
    args.add("--output", output_file.path)
    args.add("--inline-patch", patch_file.path)

    inputs = [ctx.file.base, patch_file]

    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = inputs,
        outputs = [output_file],
        mnemonic = "JsonRemove",
        progress_message = "Removing JSON value for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([output_file]))]

json_add = rule(
    implementation = _json_add_impl,
    attrs = {
        "base": attr.label(
            doc = "Base JSON file",
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "path": attr.string(
            doc = "JSON path to add value at",
            mandatory = True,
        ),
        "value": attr.string(
            doc = "JSON value to add (as JSON string, e.g. '\"hello\"' or '{\"key\": \"val\"}')",
            mandatory = False,
        ),
        "value_file": attr.label(
            doc = "File containing JSON value to add",
            allow_single_file = [".json"],
            mandatory = False,
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
    doc = """Add a value to a JSON document at the specified path.""",
)

json_replace = rule(
    implementation = _json_replace_impl,
    attrs = {
        "base": attr.label(
            doc = "Base JSON file",
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "path": attr.string(
            doc = "JSON path to replace value at",
            mandatory = True,
        ),
        "value": attr.string(
            doc = "JSON value to replace with (as JSON string)",
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
    doc = """Replace a value in a JSON document at the specified path.""",
)

json_remove = rule(
    implementation = _json_remove_impl,
    attrs = {
        "base": attr.label(
            doc = "Base JSON file",
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "path": attr.string(
            doc = "JSON path to remove",
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
    doc = """Remove a value from a JSON document at the specified path.""",
)
