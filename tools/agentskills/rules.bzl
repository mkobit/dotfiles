"""
Bazel rules for agentskills.io
"""

load("@tar.bzl", "tar")
load("@tar.bzl//tar:mtree.bzl", "mutate")

def _agent_skill_build_impl(ctx):
    # Only process files named "SKILL.md" as agentskills.io specifies
    markdown_files = [f for f in ctx.files.srcs if f.basename == "SKILL.md"]
    other_files = [f for f in ctx.files.srcs if f.basename != "SKILL.md"]

    output_files = []

    if not markdown_files:
        fail("No SKILL.md found in srcs for agent_skill target %s" % ctx.label)

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
    if len(json_files) > 1:
        fail("Multiple SKILL.md.json files found; only one is supported per tool_skill target.")

    json_file = json_files[0]

    # Output as SKILL.md in a named subdirectory for clean tar packaging.
    output_md = ctx.actions.declare_file(ctx.label.name + "_output/SKILL.md")

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
    tool_tags = ["tool:claude"] + extra_tags
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

def _gemini_extension_impl(ctx):
    # Locate the gemini-extension.json file within srcs
    extension_json = None
    for f in ctx.files.srcs:
        if f.path.endswith(ctx.attr.extension_json):
            extension_json = f
            break

    if not extension_json:
        fail("Could not find the {} file in srcs".format(ctx.attr.extension_json))

    # Generate the output JSON file safely within the current package
    output_json = ctx.actions.declare_file(ctx.label.name + "_" + extension_json.basename + ".json")

    args = ctx.actions.args()
    args.add(extension_json.path)
    args.add(output_json.path)

    ctx.actions.run(
        inputs = ctx.files.srcs,
        outputs = [output_json],
        arguments = [args],
        executable = ctx.executable._processor,
        progress_message = "Processing Gemini extension %s" % extension_json.short_path,
    )

    return [
        DefaultInfo(files = depset(ctx.files.srcs)),
        OutputGroupInfo(
            json_files = depset([output_json]),
            raw_assets = depset(ctx.files.srcs),
        ),
    ]

gemini_extension = rule(
    implementation = _gemini_extension_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True, mandatory = True),
        "extension_json": attr.string(default = "gemini-extension.json"),
        "_processor": attr.label(
            default = Label("//tools/agentskills:process_gemini_extension"),
            executable = True,
            cfg = "exec",
        ),
    },
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
    tool_tags = ["tool:gemini"] + extra_tags
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
    tool_tags = ["tool:cursor"] + extra_tags
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

def _claude_from_gemini_extension_files_impl(ctx):
    extension = ctx.attr.extension
    json_files = extension[OutputGroupInfo].json_files.to_list()
    raw_assets = extension[OutputGroupInfo].raw_assets.to_list()

    if not json_files:
        fail("No json_files found in the gemini_extension target.")

    context_json = json_files[0]

    # Find TOML command files from the raw assets (any Gemini extension stores
    # slash commands as TOML files under a commands/ subdirectory).
    command_tomls = [
        f
        for f in raw_assets
        if "/commands/" in f.short_path and f.path.endswith(".toml")
    ]

    if not command_tomls:
        fail("No TOML command files found under commands/ in the gemini_extension target.")

    install_name = ctx.attr.install_name
    command_outputs = []

    for toml_file in command_tomls:
        cmd_name = toml_file.basename[:-5]  # strip .toml
        output_md = ctx.actions.declare_file(install_name + "_commands/" + cmd_name + ".md")
        command_outputs.append(output_md)

        args = ctx.actions.args()
        args.add(toml_file.path)
        args.add(context_json.path)
        args.add(output_md.path)

        ctx.actions.run(
            inputs = [toml_file, context_json],
            outputs = [output_md],
            arguments = [args],
            executable = ctx.executable._command_processor,
            progress_message = "Processing extension command %s for Claude" % cmd_name,
        )

    # Generate Claude skill from the extension context body
    skill_md = ctx.actions.declare_file(install_name + "_skill/SKILL.md")
    skill_args = ctx.actions.args()
    skill_args.add(context_json.path)
    skill_args.add(skill_md.path)
    skill_args.add("--tool", "claude")
    skill_args.add("--scope", ctx.attr.scope)

    ctx.actions.run(
        inputs = [context_json],
        outputs = [skill_md],
        arguments = [skill_args],
        executable = ctx.executable._transformer,
        progress_message = "Transforming extension context to Claude skill for %s" % install_name,
    )

    return [
        DefaultInfo(files = depset(command_outputs + [skill_md])),
        OutputGroupInfo(
            commands = depset(command_outputs),
            skill = depset([skill_md]),
        ),
    ]

_claude_from_gemini_extension_files = rule(
    implementation = _claude_from_gemini_extension_files_impl,
    attrs = {
        "extension": attr.label(mandatory = True, providers = [OutputGroupInfo]),
        "install_name": attr.string(mandatory = True),
        "scope": attr.string(default = "user", values = ["user", "repo"]),
        "_command_processor": attr.label(
            default = Label("//tools/agentskills:process_extension_command"),
            executable = True,
            cfg = "exec",
        ),
        "_transformer": attr.label(
            default = Label("//tools/agentskills:transform_skill"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def claude_from_gemini_extension(name, extension, install_name = None, scope = "user", visibility = None, **kwargs):
    """
    Transforms a gemini_extension into Claude-native artifacts.

    Produces two tar archives for chezmoi external with exact = true:
      <install_name>.claude.commands.tar  ->  ~/.claude/commands/<install_name>/
      <install_name>.claude.skill.tar     ->  ~/.claude/skills/<install_name>/

    Targets are tagged tool:claude for discovery via bazel cquery.

    Args:
        name: Name of the Bazel target
        extension: Label of the gemini_extension target
        install_name: Install directory name (defaults to name)
        scope: Scope of the skill ("user" or "repo")
        visibility: Visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name

    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude"] + extra_tags

    # Rule that produces individual command .md files and skill SKILL.md.
    _claude_from_gemini_extension_files(
        name = name + "_files",
        extension = extension,
        install_name = install_name,
        scope = scope,
        **kwargs
    )

    # Filegroups select the two output groups so tar.bzl can bundle them separately.
    native.filegroup(
        name = name + "_command_files",
        srcs = [":" + name + "_files"],
        output_group = "commands",
        **kwargs
    )

    native.filegroup(
        name = name + "_skill_files",
        srcs = [":" + name + "_files"],
        output_group = "skill",
        **kwargs
    )

    # Hermetic tar archives via tar.bzl (BSD tar, no run_shell).
    # strip_prefix removes the generated subdirectory so archives contain flat basenames.
    tar(
        name = name + "_commands_tar",
        srcs = [":" + name + "_command_files"],
        out = install_name + ".claude.commands.tar",
        mutate = mutate(
            strip_prefix = native.package_name() + "/" + install_name + "_commands",
        ),
        tags = tool_tags,
        **kwargs
    )

    tar(
        name = name + "_skill_tar",
        srcs = [":" + name + "_skill_files"],
        out = install_name + ".claude.skill.tar",
        mutate = mutate(
            strip_prefix = native.package_name() + "/" + install_name + "_skill",
        ),
        tags = tool_tags,
        **kwargs
    )

    # Canonical target groups both archives.
    native.filegroup(
        name = name,
        srcs = [
            ":" + name + "_commands_tar",
            ":" + name + "_skill_tar",
        ],
        tags = tool_tags,
        visibility = visibility,
        **kwargs
    )
