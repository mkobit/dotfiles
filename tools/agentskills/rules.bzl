"""
Bazel rules for agentskills.io
"""

load("//tools/validation:json_schema_validation.bzl", "json_schema_validation_test")

def _agent_skill_build_impl(ctx):
    input_md = ctx.file.src
    output_json = ctx.actions.declare_file(ctx.label.name + "_frontmatter.json")

    args = ctx.actions.args()
    args.add(input_md.path)
    args.add(output_json.path)

    ctx.actions.run(
        inputs = [input_md],
        outputs = [output_json],
        arguments = [args],
        executable = ctx.executable._extractor,
        progress_message = "Extracting frontmatter from %s" % input_md.short_path,
    )

    return [
        DefaultInfo(files = depset([output_json])),
    ]

agent_skill_build = rule(
    implementation = _agent_skill_build_impl,
    attrs = {
        "src": attr.label(allow_single_file = [".md"], mandatory = True),
        "_extractor": attr.label(
            default = Label("//tools/agentskills:extract_frontmatter"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def agent_skill(name, src, visibility = None):
    """
    Builds and validates an agentskills.io skill file.

    Args:
        name: Name of the target
        src: The markdown skill file
        visibility: The visibility of the target
    """
    build_target_name = name + "_build"

    agent_skill_build(
        name = build_target_name,
        src = src,
        visibility = visibility,
    )

    json_schema_validation_test(
        name = name + "_test",
        srcs = [build_target_name],
        schema = "//tools/agentskills:schema.json",
        visibility = visibility,
    )
