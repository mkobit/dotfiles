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

def _tool_skill_impl(ctx):
    # Retrieve the OutputGroupInfo from the depended agent_skill
    agent_skill_target = ctx.attr.skill
    if OutputGroupInfo not in agent_skill_target:
        fail("The 'skill' attribute must point to an agent_skill target.")

    json_files = agent_skill_target[OutputGroupInfo].json_files.to_list()
    if not json_files:
        fail("No json_files found in the agent_skill target.")

    # There should typically be exactly one SKILL.md.json per agent_skill,
    # but the rule structure allows for multiple markdown files.
    output_files = []

    for json_file in json_files:
        # Reconstruct the original name without the .md.json suffix
        # Use target name as prefix to prevent conflicting outputs from same source file
        base_name = json_file.basename
        if base_name.endswith(".md.json"):
            new_basename = ctx.label.name + "_" + base_name[:-8] + "." + ctx.attr.tool + ".md"
        else:
            new_basename = ctx.label.name + "_" + base_name + "." + ctx.attr.tool + ".md"

        output_md = ctx.actions.declare_file(new_basename)
        output_files.append(output_md)

        args = ctx.actions.args()
        args.add(json_file.path)
        args.add(output_md.path)
        args.add("--tool", ctx.attr.tool)
        args.add("--scope", ctx.attr.scope)

        ctx.actions.run(
            inputs = [json_file],
            outputs = [output_md],
            arguments = [args],
            executable = ctx.executable._transformer,
            progress_message = "Transforming %s for %s (%s scope)" % (json_file.short_path, ctx.attr.tool, ctx.attr.scope),
        )

    return [
        DefaultInfo(files = depset(output_files)),
    ]

_tool_skill = rule(
    implementation = _tool_skill_impl,
    attrs = {
        "skill": attr.label(mandatory = True, providers = [OutputGroupInfo]),
        "tool": attr.string(mandatory = True, values = ["claude", "gemini", "cursor"]),
        "scope": attr.string(default = "user", values = ["user", "repo"]),
        "_transformer": attr.label(
            default = Label("//tools/agentskills:transform_skill"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def claude_skill(name, skill, scope = "user", visibility = None):
    """
    Transforms an agent_skill into a format suitable for Claude.

    Args:
        name: Name of the target
        skill: Label of the agent_skill target
        scope: Scope of the skill ("user" or "repo")
        visibility: The visibility of the target
    """
    _tool_skill(
        name = name,
        skill = skill,
        tool = "claude",
        scope = scope,
        visibility = visibility,
    )

def gemini_skill(name, skill, scope = "user", visibility = None):
    """
    Transforms an agent_skill into a format suitable for Gemini.

    Args:
        name: Name of the target
        skill: Label of the agent_skill target
        scope: Scope of the skill ("user" or "repo")
        visibility: The visibility of the target
    """
    _tool_skill(
        name = name,
        skill = skill,
        tool = "gemini",
        scope = scope,
        visibility = visibility,
    )
