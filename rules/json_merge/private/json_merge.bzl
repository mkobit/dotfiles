"""
Core JSON merge rule implementation.

Provides deterministic JSON merging capabilities with configurable strategies,
suitable for Bazel's hermetic build requirements.
"""

def _json_merge_impl(ctx):
    """Implementation for json_merge rule."""

    # Declare output file
    output_file = ctx.actions.declare_file(ctx.attr.out)

    # Prepare arguments for the merge tool
    args = ctx.actions.args()
    args.add("--output", output_file.path)
    args.add("--strategy", ctx.attr.strategy)

    if ctx.attr.validate_claude_hooks:
        args.add("--validate-hooks")

    args.add("--inputs")
    args.add_all([f.path for f in ctx.files.srcs])

    if ctx.file.merge_document:
        args.add("--merge-document", ctx.file.merge_document.path)

    # Prepare inputs for the action
    inputs = ctx.files.srcs[:]
    if ctx.file.merge_document:
        inputs.append(ctx.file.merge_document)

    # Execute merge tool
    ctx.actions.run(
        executable = ctx.executable._json_merge_tool,
        arguments = [args],
        inputs = inputs,
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
        "merge_document": attr.label(
            doc = "Optional JSON merge document to apply after merging srcs",
            allow_single_file = [".json"],
            mandatory = False,
        ),
        "out": attr.string(
            doc = "Output filename",
            mandatory = True,
        ),
        "strategy": attr.string(
            doc = "Merge strategy (deep_merge, claude_hooks)",
            default = "deep_merge",
            values = ["deep_merge", "claude_hooks"],
        ),
        "validate_claude_hooks": attr.bool(
            doc = "Validate output as Claude hooks format",
            default = False,
        ),
        "_json_merge_tool": attr.label(
            executable = True,
            cfg = "exec",
            default = Label("//rules/json_merge:json_merge_tool"),
        ),
    },
    doc = """
    Merge multiple JSON files into a single output file.
    
    The rule merges JSON files in the order specified in 'srcs', with later files
    taking precedence over earlier ones. An optional merge document can be applied
    as the final merge step.
    
    Example:
        json_merge(
            name = "merged_config",
            srcs = [
                "base_config.json",
                "env_specific.json",
            ],
            merge_document = "overrides.json",
            out = "final_config.json",
            strategy = "deep_merge",
        )
        
        # Claude hooks specific merge
        json_merge(
            name = "merged_hooks",
            srcs = [
                "base_hooks.json",
                "tool_specific_hooks.json", 
            ],
            out = "claude_hooks.json",
            strategy = "claude_hooks",
            validate_claude_hooks = True,
        )
    """,
)
