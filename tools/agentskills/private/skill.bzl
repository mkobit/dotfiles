"""Private implementations for individual agent skill rules."""

load("@tar.bzl", "tar")
load("@tar.bzl//tar:mtree.bzl", "mutate")
load("//tools/chezmoi:defs.bzl", "ChezmoidTags")

def _agent_skill_build_impl(ctx):
    # Only process files named "SKILL.md" as agentskills.io specifies
    markdown_files = [f for f in ctx.files.srcs if f.basename == "SKILL.md"]
    other_files = [f for f in ctx.files.srcs if f.basename != "SKILL.md"]

    output_files = []

    if not markdown_files:
        fail("No SKILL.md found in srcs for agent_skill target %s" % ctx.label)

    for md_file in markdown_files:
        # Generate the IR JSON output named after the skill directory.
        # E.g. src/ai/skills/my-skill/SKILL.md -> src/ai/skills/my-skill/SKILL.md.ir.json
        output_json = ctx.actions.declare_file(md_file.short_path + ".ir.json")
        output_files.append(output_json)

        args = ctx.actions.args()

        # Pass the skill directory (dirname of SKILL.md), not the file itself
        args.add(md_file.dirname)
        args.add(output_json.path)
        args.add("--source-format")
        args.add("agentskills.io")

        ctx.actions.run(
            inputs = ctx.files.srcs,
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

def _agent_build_impl(ctx):
    """Runs process_agent on a single agent .md file, emitting AgentIR JSON."""
    md_file = ctx.file.src

    output_json = ctx.actions.declare_file(md_file.short_path + ".ir.json")

    args = ctx.actions.args()
    args.add(md_file.path)
    args.add(output_json.path)
    args.add("--source-format")
    args.add(ctx.attr.source_format)

    ctx.actions.run(
        inputs = [md_file],
        outputs = [output_json],
        arguments = [args],
        executable = ctx.executable._processor,
        progress_message = "Processing agent %s" % md_file.short_path,
    )

    return [
        DefaultInfo(files = depset([md_file])),
        OutputGroupInfo(
            json_files = depset([output_json]),
        ),
    ]

agent_build = rule(
    implementation = _agent_build_impl,
    attrs = {
        "src": attr.label(allow_single_file = [".md"], mandatory = True),
        "source_format": attr.string(default = "claude-agents", values = ["claude-agents", "claude-plugin"]),
        "_processor": attr.label(
            default = Label("//tools/agentskills:process_agent"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def _tool_agent_impl(ctx):
    agent_target = ctx.attr.agent
    if OutputGroupInfo not in agent_target:
        fail("The 'agent' attribute must point to an agent_build target.")

    json_files = agent_target[OutputGroupInfo].json_files.to_list()
    if not json_files:
        fail("No json_files found in the agent_build target.")
    if len(json_files) > 1:
        fail("Multiple AgentIR JSON files found; only one is supported per _tool_agent target.")

    json_file = json_files[0]

    # Output as <name>.md in a named subdirectory for clean tar packaging.
    output_md = ctx.actions.declare_file(ctx.label.name + "_output/" + ctx.attr.output_name + ".md")

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
        progress_message = "Transforming agent %s for %s (%s scope)" % (json_file.short_path, ctx.attr.tool, ctx.attr.scope),
    )

    return [
        DefaultInfo(files = depset([output_md])),
    ]

_tool_agent = rule(
    implementation = _tool_agent_impl,
    attrs = {
        "agent": attr.label(mandatory = True, providers = [OutputGroupInfo]),
        "tool": attr.string(mandatory = True, values = ["claude", "gemini", "cursor"]),
        "scope": attr.string(default = "user", values = ["user", "repo"]),
        "output_name": attr.string(mandatory = True),
        "_transformer": attr.label(
            default = Label("//tools/agentskills:transform_agent"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def _tool_skill_impl(ctx):
    # Retrieve the OutputGroupInfo from the depended agent_skill
    agent_skill_target = ctx.attr.skill
    if OutputGroupInfo not in agent_skill_target:
        fail("The 'skill' attribute must point to an agent_skill target.")

    json_files = agent_skill_target[OutputGroupInfo].json_files.to_list()
    if not json_files:
        fail("No json_files found in the agent_skill target.")
    if len(json_files) > 1:
        fail("Multiple SKILL.md.ir.json files found; only one is supported per tool_skill target.")

    json_file = json_files[0]
    raw_assets = agent_skill_target[OutputGroupInfo].raw_assets.to_list()

    # Output as SKILL.md in a named subdirectory for clean tar packaging.
    output_md = ctx.actions.declare_file(ctx.label.name + "_output/SKILL.md")

    args = ctx.actions.args()
    args.add(json_file.path)
    args.add(output_md.path)
    args.add("--tool", ctx.attr.tool)
    args.add("--scope", ctx.attr.scope)

    ctx.actions.run(
        inputs = [json_file] + raw_assets,
        outputs = [output_md],
        arguments = [args],
        executable = ctx.executable._transformer,
        progress_message = "Transforming %s for %s (%s scope)" % (json_file.short_path, ctx.attr.tool, ctx.attr.scope),
    )

    return [
        DefaultInfo(files = depset([output_md])),
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

def claude_skill(name, skill, scope = "user", install_name = None, visibility = None, **kwargs):
    """
    Transforms an agent_skill into a format suitable for Claude.
    Produces <install_name>.claude.skill.tar tagged tool:claude.

    Args:
        name: Name of the target
        skill: Label of the agent_skill target
        scope: Scope of the skill ("user" or "repo")
        install_name: Install directory name (defaults to name)
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude", ChezmoidTags.claude_skill] + extra_tags
    files_target = name + "_files"

    _tool_skill(
        name = files_target,
        skill = skill,
        tool = "claude",
        scope = scope,
        **kwargs
    )

    tar(
        name = name + "_tar",
        srcs = [":" + files_target],
        out = install_name + ".claude.skill.tar",
        mutate = mutate(strip_prefix = native.package_name() + "/" + files_target + "_output"),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
        **kwargs
    )

def gemini_skill(name, skill, scope = "user", install_name = None, visibility = None, **kwargs):
    """
    Transforms an agent_skill into a format suitable for Gemini.
    Produces <install_name>.gemini.skill.tar tagged tool:gemini.

    Args:
        name: Name of the target
        skill: Label of the agent_skill target
        scope: Scope of the skill ("user" or "repo")
        install_name: Install directory name (defaults to name)
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:gemini", ChezmoidTags.gemini_skill] + extra_tags
    files_target = name + "_files"

    _tool_skill(
        name = files_target,
        skill = skill,
        tool = "gemini",
        scope = scope,
        **kwargs
    )

    tar(
        name = name + "_tar",
        srcs = [":" + files_target],
        out = install_name + ".gemini.skill.tar",
        mutate = mutate(strip_prefix = native.package_name() + "/" + files_target + "_output"),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
        **kwargs
    )

def cursor_skill(name, skill, scope = "user", install_name = None, visibility = None, **kwargs):
    """
    Transforms an agent_skill into a format suitable for Cursor.
    Produces <install_name>.cursor.skill.tar tagged tool:cursor.

    Args:
        name: Name of the target
        skill: Label of the agent_skill target
        scope: Scope of the skill ("user" or "repo")
        install_name: Install directory name (defaults to name)
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:cursor", ChezmoidTags.cursor_skill] + extra_tags
    files_target = name + "_files"

    _tool_skill(
        name = files_target,
        skill = skill,
        tool = "cursor",
        scope = scope,
        **kwargs
    )

    tar(
        name = name + "_tar",
        srcs = [":" + files_target],
        out = install_name + ".cursor.skill.tar",
        mutate = mutate(strip_prefix = native.package_name() + "/" + files_target + "_output"),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
        **kwargs
    )

def claude_agent(name, src, install_name = None, scope = "user", source_format = "claude-agents", visibility = None, **kwargs):
    """
    Processes a single agent .md file through the IR pipeline and packages it for Claude.

    Runs process_agent → AgentIR → transform_agent → <install_name>.claude.agents.tar
    tagged tool:claude-agents.

    Args:
        name: Name of the target
        src: Label of the single agent .md file
        install_name: Output filename stem for the agent (defaults to name)
        scope: Scope of the agent ("user" or "repo")
        source_format: Source format passed to process_agent ("claude-agents" or "claude-plugin")
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude-agents", ChezmoidTags.claude_agents] + extra_tags

    build_target = name + "_build"
    files_target = name + "_files"

    # agent_build is a custom rule with a fixed attr set; pass only what it accepts.
    agent_build(
        name = build_target,
        src = src,
        source_format = source_format,
    )

    _tool_agent(
        name = files_target,
        agent = ":" + build_target,
        tool = "claude",
        scope = scope,
        output_name = install_name,
        **kwargs
    )

    tar(
        name = name + "_tar",
        srcs = [":" + files_target],
        out = install_name + ".claude.agents.tar",
        mutate = mutate(strip_prefix = native.package_name() + "/" + files_target + "_output"),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
        **kwargs
    )
