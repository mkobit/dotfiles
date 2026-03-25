"""
Bazel rules for agentskills.io
"""

def _agent_skill_build_impl(ctx):
    # Separate the markdown files (to be processed) from other files (to be passed through)
    markdown_files = [f for f in ctx.files.srcs if f.path.endswith(".md")]
    other_files = [f for f in ctx.files.srcs if not f.path.endswith(".md")]

    output_files = []

    for md_file in markdown_files:
        # Generate the output JSON file alongside the input markdown
        # E.g. SKILL.md -> SKILL.md.json
        output_json = ctx.actions.declare_file(md_file.short_path + ".json")
        output_files.append(output_json)

        args = ctx.actions.args()
        args.add(md_file.path)
        args.add(output_json.path)

        ctx.actions.run(
            inputs = [md_file],
            outputs = [output_json],
            arguments = [args],
            executable = ctx.executable._processor,
            progress_message = "Processing and validating %s" % md_file.short_path,
        )

    # DefaultInfo returns the original sources unchanged, as dependencies
    # typically expect to operate on the original files.
    # OutputGroupInfo explicitly separates JSON derivatives from raw asset files,
    # enabling multivariant outputs across tooling.
    return [
        DefaultInfo(files = depset(ctx.files.srcs)),
        OutputGroupInfo(
            json_files = depset(output_files),
            raw_assets = depset(other_files),
        ),
    ]

agent_skill_build = rule(
    implementation = _agent_skill_build_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True, mandatory = True),
        "_processor": attr.label(
            default = Label("//tools/agentskills:process_skill"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def agent_skill(name, srcs, visibility = None):
    """
    Builds and validates an agentskills.io skill directory.

    Args:
        name: Name of the target
        srcs: A list of files making up the skill (e.g., glob(["**/*"]))
        visibility: The visibility of the target
    """
    build_target_name = name + ".build"

    agent_skill_build(
        name = build_target_name,
        srcs = srcs,
        visibility = visibility,
    )

    native.alias(
        name = name,
        actual = build_target_name,
        visibility = visibility,
    )
