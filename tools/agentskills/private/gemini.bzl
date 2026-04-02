"""Private implementations for Gemini extension ingestion rules."""

load("@tar.bzl", "tar")
load("@tar.bzl//tar:mtree.bzl", "mutate")
load("//tools/chezmoi:defs.bzl", "CHEZMOI_TOMBSTONE")

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

def claude_from_gemini_extension(name, extension, install_name = None, scope = "user", visibility = None, tombstone = False, **kwargs):
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
        tombstone: If True, marks both output tars for removal by chezmoi.
            Causes chezmoi apply to delete commands/<install_name>/ and
            skills/<install_name>/ from the destination.
        **kwargs: Passed through (e.g. target_compatible_with)
    """
    if install_name == None:
        install_name = name

    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude"] + ([CHEZMOI_TOMBSTONE] if tombstone else []) + extra_tags

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
