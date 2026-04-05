"""Private implementations for skill collection and subagent rules."""

load("@tar.bzl", "tar")
load("@tar.bzl//tar:mtree.bzl", "mutate")
load("//tools/chezmoi:defs.bzl", "ChezmoidTags")

def claude_skill_group(name, srcs, namespace, install_name = None, strip_prefix = "", visibility = None, **kwargs):
    """
    Packages an entire skill collection as a namespaced tree for Claude.

    Produces <install_name>.claude.skill-group.tar tagged tool:claude and skill-group:<namespace>.
    The archive contents are relative paths within the collection (e.g. qa/SKILL.md,
    review/SKILL.md) with no leading namespace prefix — chezmoi installs the archive
    to skills/<install_name>/ using the entry key.

    For files from an external repo @gstack, the short_path prefix is "../gstack",
    so pass strip_prefix = "../gstack". The caller knows the external repo name.

    Args:
        name: Name of the target
        srcs: A label list of files from the collection (e.g. ["@gstack//:all"])
        namespace: Namespace string (e.g. "gstack") — used for tagging
        install_name: Install directory name under skills/ (defaults to namespace)
        strip_prefix: Path prefix to strip from file short_paths. For external repos
            @foo, use "../foo". For local files, use native.package_name() or "".
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with, tags)
    """
    if install_name == None:
        install_name = namespace
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude", "skill-group:" + namespace, ChezmoidTags.claude_collection] + extra_tags

    tar(
        name = name + "_tar",
        srcs = srcs,
        out = install_name + ".claude.skill-group.tar",
        mutate = mutate(strip_prefix = strip_prefix),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
    )

def claude_skill_item(name, srcs, namespace, install_name = None, strip_prefix = "", visibility = None, **kwargs):
    """
    Packages a single skill cherry-picked from a collection for Claude.

    Produces <install_name>.claude.skill.tar tagged tool:claude and skill-group:<namespace>.
    Uses the .claude.skill.tar suffix so existing chezmoi templates handle it automatically
    (installing to skills/<install_name>/).

    For files from an external repo @gstack under qa/, pass
    strip_prefix = "../gstack/qa" to strip the repo and skill subdirectory prefix.

    Args:
        name: Name of the target
        srcs: A label list of files for this individual skill
        namespace: Namespace the skill belongs to (e.g. "gstack") — used for tagging
        install_name: Install directory name under skills/ (defaults to namespace + "-" + name)
        strip_prefix: Path prefix to strip from file short_paths.
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with, tags)
    """
    if install_name == None:
        install_name = namespace + "-" + name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude", "skill-group:" + namespace, ChezmoidTags.claude_skill] + extra_tags

    tar(
        name = name + "_tar",
        srcs = srcs,
        out = install_name + ".claude.skill.tar",
        mutate = mutate(strip_prefix = strip_prefix),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
    )

def claude_subagent_group(name, srcs, install_name = None, strip_prefix = "", visibility = None, **kwargs):
    """
    Packages a collection of Claude sub-agent .md files for installation to ~/.claude/agents/.

    Produces <install_name>.claude.agents.tar tagged tool:claude-agents.
    The archive should contain flat .md files with no subdirectories.

    For files from an external repo @agency_agents under engineering/, pass
    strip_prefix = "../agency_agents/engineering" to produce flat agent .md files.

    Args:
        name: Name of the target
        srcs: A label list of sub-agent .md files
        install_name: Base name for the output tar (defaults to name)
        strip_prefix: Path prefix to strip from file short_paths.
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with, tags)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude-agents", ChezmoidTags.claude_agents] + extra_tags

    tar(
        name = name + "_tar",
        srcs = srcs,
        out = install_name + ".claude.agents.tar",
        mutate = mutate(strip_prefix = strip_prefix),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
    )

def claude_plugin_commands(name, srcs, install_name = None, strip_prefix = "", visibility = None, **kwargs):
    """
    Packages a plugin's commands/ directory for installation to ~/.claude/commands/<install_name>/.

    Produces <install_name>.claude.commands.tar tagged claude:commands.

    Args:
        name: Name of the target
        srcs: A label list of command .md files
        install_name: Install subdirectory name under commands/ (defaults to name)
        strip_prefix: Path prefix to strip from file short_paths
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with, tags)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude", ChezmoidTags.claude_commands] + extra_tags

    tar(
        name = name + "_tar",
        srcs = srcs,
        out = install_name + ".claude.commands.tar",
        mutate = mutate(strip_prefix = strip_prefix),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
    )

def claude_subagent(name, srcs, install_name = None, strip_prefix = "", visibility = None, **kwargs):
    """
    Packages a single Claude sub-agent .md file for installation to ~/.claude/agents/.

    Produces <install_name>.claude.agents.tar tagged tool:claude-agents.

    Args:
        name: Name of the target
        srcs: A label list containing the single sub-agent .md file
        install_name: Base name for the output tar (defaults to name)
        strip_prefix: Path prefix to strip from the file short_path.
        visibility: The visibility of the target
        **kwargs: Passed through (e.g. target_compatible_with, tags)
    """
    if install_name == None:
        install_name = name
    extra_tags = kwargs.pop("tags", [])
    tool_tags = ["tool:claude-agents", ChezmoidTags.claude_agents] + extra_tags

    tar(
        name = name + "_tar",
        srcs = srcs,
        out = install_name + ".claude.agents.tar",
        mutate = mutate(strip_prefix = strip_prefix),
        tags = tool_tags,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [":" + name + "_tar"],
        tags = tool_tags,
        visibility = visibility,
    )
