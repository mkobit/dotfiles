"""
Module extension for declaring external AI skill repositories.

Usage in MODULE.bazel:

    ai_skills = use_extension("//tools/agentskills:extensions.bzl", "ai_skills")

    # Preferred: GitHub shorthand (derives urls and strip_prefix automatically)
    ai_skills.claude_plugin(
        name = "compound_engineering",
        github = "EveryInc/compound-engineering-plugin",
        tag = "compound-engineering-v2.62.0",
        sha256 = "...",
        plugin_path = "plugins/compound-engineering",
    )

    ai_skills.claude_agents(
        name = "agency_agents",
        github = "msitarzewski/agency-agents",
        commit = "4feb0cd...",
        sha256 = "...",
    )

    # Fallback: explicit urls/strip_prefix for non-GitHub sources
    ai_skills.claude_plugin(
        name = "my_plugin",
        urls = ["https://example.com/plugin.tar.gz"],
        strip_prefix = "plugin-1.0.0",
        sha256 = "...",
    )

    # Claude plugin marketplace (embedded plugins only; external ones need separate claude_plugin entries)
    ai_skills.claude_marketplace(
        name = "my_marketplace",
        github = "owner/marketplace-repo",
        tag = "v1.0.0",
        sha256 = "...",
        marketplace_json = ".claude-plugin/marketplace.json",
    )

    use_repo(ai_skills, "compound_engineering", "agency_agents", "my_marketplace")
"""

def _resolve_github(tag):
    """Derive urls and strip_prefix from github + tag or commit shorthand.

    Returns (urls, strip_prefix) ready to pass to ctx.download_and_extract.
    Falls back to explicit tag.urls / tag.strip_prefix for non-GitHub sources.
    """
    if not tag.github:
        return tag.urls, tag.strip_prefix
    repo_name = tag.github.split("/")[-1]
    if tag.tag:
        url = "https://github.com/{}/archive/refs/tags/{}.tar.gz".format(tag.github, tag.tag)

        # GitHub strips a leading 'v' from the tag when naming the extracted directory.
        dir_tag = tag.tag[1:] if tag.tag.startswith("v") else tag.tag
        strip_prefix = "{}-{}".format(repo_name, dir_tag)
    else:
        url = "https://github.com/{}/archive/{}.tar.gz".format(tag.github, tag.commit)
        strip_prefix = "{}-{}".format(repo_name, tag.commit)
    return [url], strip_prefix

# Common GitHub shorthand attrs shared across all tag classes.
_GITHUB_ATTRS = {
    "github": attr.string(default = "", doc = "GitHub repo as 'owner/repo'. Derives urls and strip_prefix automatically."),
    "tag": attr.string(default = "", doc = "Git tag (use with github). Generates a refs/tags URL."),
    "commit": attr.string(default = "", doc = "Git commit SHA (use with github when no tag exists)."),
    "urls": attr.string_list(default = [], doc = "Explicit download URLs. Required when github is not set."),
    "strip_prefix": attr.string(default = "", doc = "Explicit strip prefix. Required when github is not set."),
}

def _anthropics_skills_repo_impl(ctx):
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    build_content = """load("@//tools/agentskills:defs.bzl", "agent_skill")

"""

    # Traverse using Starlark's path API instead of relying on bash/find
    # This ensures cross-platform compatibility without external dependencies.
    skills_dir = ctx.path("skills")
    if skills_dir.exists:
        for p in skills_dir.readdir():
            if p.is_dir:
                skill_md_path = p.get_child("SKILL.md")
                if skill_md_path.exists:
                    skill_name = p.basename
                    build_content += """
agent_skill(
    name = "{name}",
    srcs = glob(["skills/{name}/**/*"]),
    visibility = ["//visibility:public"],
)
""".format(name = skill_name)

    ctx.file("BUILD.bazel", build_content)

anthropics_skills_repo = repository_rule(
    implementation = _anthropics_skills_repo_impl,
    attrs = dict(_GITHUB_ATTRS, sha256 = attr.string(mandatory = True)),
)

def _gemini_extension_repo_impl(ctx):
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    build_content = """load("@//tools/agentskills:defs.bzl", "gemini_extension")

filegroup(
    name = "files",
    srcs = glob(["**/*"], exclude = ["BUILD.bazel", "WORKSPACE"]),
    visibility = ["//visibility:public"],
)

gemini_extension(
    name = "extension",
    srcs = [":files"],
    extension_json = "gemini-extension.json",
    visibility = ["//visibility:public"],
)
"""
    ctx.file("BUILD.bazel", build_content)

gemini_extension_repo = repository_rule(
    implementation = _gemini_extension_repo_impl,
    attrs = dict(_GITHUB_ATTRS, sha256 = attr.string(mandatory = True)),
)

def _skill_collection_repo_impl(ctx):
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    include_set = {s: True for s in ctx.attr.include} if ctx.attr.include else {}
    exclude_set = {s: True for s in ctx.attr.exclude} if ctx.attr.exclude else {}

    build_content = 'package(default_visibility = ["//visibility:public"])\n\n'

    # Find skill subdirectories (those containing a SKILL.md), sorted for reproducibility.
    all_skill_names = []
    root_dir = ctx.path(".")
    for entry in sorted(root_dir.readdir(), key = lambda e: e.basename):
        if entry.is_dir:
            skill_md = entry.get_child("SKILL.md")
            if skill_md.exists:
                all_skill_names.append(entry.basename)
                build_content += """
filegroup(
    name = "{name}",
    srcs = glob(["{name}/**/*"]),
)
""".format(name = entry.basename)

    # Apply include/exclude to determine which skills the :skills aggregator exposes.
    # include takes precedence: if non-empty, only listed skills are selected.
    # Otherwise exclude removes named skills from the full set.
    if include_set:
        selected_names = [n for n in all_skill_names if n in include_set]
    elif exclude_set:
        selected_names = [n for n in all_skill_names if n not in exclude_set]
    else:
        selected_names = list(all_skill_names)

    def _label_list(names):
        return '["' + '", "'.join([":" + n for n in names]) + '"]' if names else "[]"

    build_content += """
filegroup(
    name = "root",
    srcs = glob(["*.md", "*.json", "*.toml"], allow_empty = True),
)

# bin: root-level bin/ directory with shared helper scripts (e.g. gstack CLI tools).
# Empty for collections that have no root bin/. Include alongside :skills in
# claude_skill_group srcs so helpers land at skills/<namespace>/bin/.
filegroup(
    name = "bin",
    srcs = glob(["bin/**/*"], allow_empty = True),
)

# skills: the configured selection (include/exclude from MODULE.bazel).
# Use this target in consuming BUILD files — filtering is already applied.
filegroup(
    name = "skills",
    srcs = {selected},
)

# all-skills: every discovered skill subdirectory, unfiltered.
# Useful for introspection or overriding the configured selection.
filegroup(
    name = "all-skills",
    srcs = {all_skills},
)

filegroup(
    name = "all",
    srcs = glob(
        ["**/*"],
        exclude = ["BUILD.bazel", "WORKSPACE", "WORKSPACE.bazel", "node_modules/**", ".git/**"],
    ),
)
""".format(
        selected = _label_list(selected_names),
        all_skills = _label_list(all_skill_names),
    )
    ctx.file("BUILD.bazel", build_content)

    # Emit skills.bzl for load-time introspection.
    # SKILLS = all discovered skills; SELECTED_SKILLS = after include/exclude.
    # Consumers can load these for further Starlark-level filtering if needed.
    skills_bzl = "# Auto-generated by skill_collection repository rule. Do not edit.\n"
    skills_bzl += "SKILLS = [\n"
    for name in all_skill_names:
        skills_bzl += '    "{}",\n'.format(name)
    skills_bzl += "]\n\n"
    skills_bzl += "SELECTED_SKILLS = [\n"
    for name in selected_names:
        skills_bzl += '    "{}",\n'.format(name)
    skills_bzl += "]\n"
    ctx.file("skills.bzl", skills_bzl)

skill_collection_repo = repository_rule(
    implementation = _skill_collection_repo_impl,
    attrs = dict(
        _GITHUB_ATTRS,
        sha256 = attr.string(mandatory = True),
        include = attr.string_list(default = [], doc = "If non-empty, only these skill names appear in :skills."),
        exclude = attr.string_list(default = [], doc = "Skill names to omit from :skills. Ignored when include is set."),
    ),
)

def _claude_agents_repo_impl(ctx):
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    build_content = 'package(default_visibility = ["//visibility:public"])\n\n'

    _SKIP_DIRS = ["scripts", "examples", "integrations", "docs", "node_modules"]

    root_dir = ctx.path(".")
    division_names = []

    for division_entry in root_dir.readdir():
        if not division_entry.is_dir:
            continue
        basename = division_entry.basename
        if basename.startswith(".") or basename in _SKIP_DIRS:
            continue

        agent_files = []
        for agent_entry in division_entry.readdir():
            if agent_entry.basename.endswith(".md"):
                agent_files.append(agent_entry)
                agent_name = agent_entry.basename[:-3]  # strip .md
                build_content += """
filegroup(
    name = "{name}",
    srcs = ["{division}/{file}"],
)
""".format(name = agent_name, division = basename, file = agent_entry.basename)

        if agent_files:
            division_names.append(basename)
            build_content += """
filegroup(
    name = "{division}",
    srcs = glob(["{division}/*.md"]),
)
""".format(division = basename)

    build_content += """
filegroup(
    name = "all",
    srcs = glob(["*/*.md"]),
)
"""
    ctx.file("BUILD.bazel", build_content)

claude_agents_repo = repository_rule(
    implementation = _claude_agents_repo_impl,
    attrs = dict(_GITHUB_ATTRS, sha256 = attr.string(mandatory = True)),
)

def _claude_plugin_repo_impl(ctx):
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    # plugin_path locates the plugin root within the extracted archive.
    # For single-plugin repos it is "" (the root itself).
    # For multi-plugin repos (e.g. compound: plugins/compound-engineering) pass the subpath.
    plugin_path = ctx.attr.plugin_path
    if plugin_path:
        plugin_root = ctx.path(plugin_path)
        path_prefix = plugin_path + "/"
    else:
        plugin_root = ctx.path(".")
        path_prefix = ""

    build_content = 'package(default_visibility = ["//visibility:public"])\n\n'

    # Read plugin name from .claude-plugin/plugin.json if present.
    plugin_name = ctx.attr.name
    for manifest_dir in [".claude-plugin", ".cursor-plugin"]:
        manifest_path = plugin_root.get_child(manifest_dir).get_child("plugin.json")
        if manifest_path.exists:
            manifest = json.decode(ctx.read(manifest_path))
            plugin_name = manifest.get("name", ctx.attr.name)
            break

    build_content += "# Plugin: {}\n\n".format(plugin_name)

    # --- Skills: <plugin_root>/skills/<name>/SKILL.md ---
    skill_names = []
    skills_dir = plugin_root.get_child("skills")
    if skills_dir.exists:
        for entry in sorted(skills_dir.readdir(), key = lambda e: e.basename):
            if entry.is_dir and entry.get_child("SKILL.md").exists:
                skill_names.append(entry.basename)
                build_content += """
filegroup(
    name = "{name}",
    srcs = glob(["{prefix}skills/{name}/**/*"]),
)
""".format(name = entry.basename, prefix = path_prefix)

    def _label_list(names):
        return '["' + '", "'.join([":" + n for n in names]) + '"]' if names else "[]"

    build_content += """
# skills: all discovered skill directories.
filegroup(
    name = "skills",
    srcs = {skills},
)
""".format(skills = _label_list(skill_names))

    # --- Agents: <plugin_root>/agents/<category>/<name>.md ---
    # Generates:
    #   :<name>          per individual agent file (atom — composable into any deployment)
    #   :agents_<cat>    per-category aggregate
    #   :agents          all agents across all categories
    agent_categories = []
    all_agent_names = []
    agents_dir = plugin_root.get_child("agents")
    if agents_dir.exists:
        for cat_entry in sorted(agents_dir.readdir(), key = lambda e: e.basename):
            if not cat_entry.is_dir:
                continue
            cat_agent_names = []
            for agent_entry in sorted(cat_entry.readdir(), key = lambda e: e.basename):
                if not agent_entry.basename.endswith(".md"):
                    continue
                agent_name = agent_entry.basename[:-3]  # strip .md
                cat_agent_names.append(agent_name)
                all_agent_names.append(agent_name)
                build_content += """
filegroup(
    name = "{agent}",
    srcs = ["{prefix}agents/{cat}/{agent}.md"],
)
""".format(agent = agent_name, cat = cat_entry.basename, prefix = path_prefix)

            if cat_agent_names:
                agent_categories.append(cat_entry.basename)
                build_content += """
# agents_{cat}: all agents in the {cat} category.
filegroup(
    name = "agents_{cat}",
    srcs = {members},
)
""".format(cat = cat_entry.basename, members = _label_list(cat_agent_names))

    build_content += """
# agents: all discovered agent files across all categories.
filegroup(
    name = "agents",
    srcs = {agents},
)
""".format(agents = _label_list(["agents_" + c for c in agent_categories]))

    # --- Commands: <plugin_root>/commands/*.md ---
    build_content += """
filegroup(
    name = "commands",
    srcs = glob(["{prefix}commands/**/*.md"], allow_empty = True),
)
""".format(prefix = path_prefix)

    ctx.file("BUILD.bazel", build_content)

claude_plugin_repo = repository_rule(
    implementation = _claude_plugin_repo_impl,
    attrs = dict(
        _GITHUB_ATTRS,
        sha256 = attr.string(mandatory = True),
        plugin_path = attr.string(default = "", doc = "Subpath within the archive to the plugin root. Empty = archive root. For multi-plugin repos (e.g. 'plugins/compound-engineering')."),
    ),
)

def _claude_marketplace_repo_impl(ctx):
    """Fetches a Claude plugin marketplace archive and generates filegroups for each embedded plugin.

    A marketplace.json lists plugins with their sources. This rule handles plugins that are
    embedded in the same archive (identified by a relative plugin_path). Externally-sourced
    plugins (github/url sources) must be declared separately via claude_plugin tag entries.
    """
    urls, strip_prefix = _resolve_github(ctx.attr)
    ctx.download_and_extract(
        url = urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = strip_prefix,
    )

    marketplace_path = ctx.attr.marketplace_json
    marketplace_file = ctx.path(marketplace_path)
    if not marketplace_file.exists:
        fail("marketplace.json not found at: {}".format(marketplace_path))

    marketplace = json.decode(ctx.read(marketplace_file))
    marketplace_root = marketplace_file.dirname

    build_content = 'package(default_visibility = ["//visibility:public"])\n\n'
    build_content += "# Marketplace: {}\n\n".format(marketplace.get("name", ctx.attr.name))

    def _label_list(names):
        return '["' + '", "'.join([":" + n for n in names]) + '"]' if names else "[]"

    plugin_names = []

    for plugin in marketplace.get("plugins", []):
        plugin_name = plugin.get("name", "")
        if not plugin_name:
            continue

        source = plugin.get("source", "")

        # Only handle embedded plugins — those whose source is a relative path within this archive.
        # External plugins (dicts with source="github"/"url"/etc.) need separate claude_plugin entries.
        if type(source) != "string":
            build_content += "# External plugin '{}' — declare separately via ai_skills.claude_plugin()\n\n".format(plugin_name)
            continue

        # Resolve plugin root: source is relative to the marketplace.json directory.
        # Treat empty source and "." as self-rooted (same directory as marketplace.json).
        normalised_source = "" if (not source or source == ".") else source
        plugin_path = marketplace_root.get_child(normalised_source) if normalised_source else marketplace_root
        if not plugin_path.exists:
            build_content += "# Plugin '{}' source path not found: {}\n\n".format(plugin_name, source)
            continue

        # Build the glob prefix: parent dir of marketplace.json + plugin source subpath.
        # Use rpartition to safely handle a marketplace.json with no directory component.
        marketplace_dir = marketplace_path.rpartition("/")[0]
        if normalised_source:
            raw_prefix = (marketplace_dir + "/" + normalised_source + "/") if marketplace_dir else (normalised_source + "/")
        else:
            raw_prefix = (marketplace_dir + "/") if marketplace_dir else ""
        path_prefix = raw_prefix.lstrip("/")

        # Skills
        skill_names = []
        skills_dir = plugin_path.get_child("skills")
        if skills_dir.exists:
            for entry in sorted(skills_dir.readdir(), key = lambda e: e.basename):
                if entry.is_dir and entry.get_child("SKILL.md").exists:
                    skill_names.append(entry.basename)
                    build_content += """
filegroup(
    name = "{plugin}_{skill}",
    srcs = glob(["{prefix}skills/{skill}/**/*"]),
)
""".format(plugin = plugin_name, skill = entry.basename, prefix = path_prefix)

        build_content += """
filegroup(
    name = "{plugin}_skills",
    srcs = {skills},
)
""".format(plugin = plugin_name, skills = _label_list([plugin_name + "_" + s for s in skill_names]))

        # Agents
        agent_categories = []
        all_agent_names = []
        agents_dir = plugin_path.get_child("agents")
        if agents_dir.exists:
            for cat_entry in sorted(agents_dir.readdir(), key = lambda e: e.basename):
                if not cat_entry.is_dir:
                    continue
                cat_agent_names = []
                for agent_entry in sorted(cat_entry.readdir(), key = lambda e: e.basename):
                    if not agent_entry.basename.endswith(".md"):
                        continue
                    agent_name = agent_entry.basename[:-3]
                    cat_agent_names.append(agent_name)
                    all_agent_names.append(agent_name)
                    build_content += """
filegroup(
    name = "{plugin}_{agent}",
    srcs = ["{prefix}agents/{cat}/{agent}.md"],
)
""".format(plugin = plugin_name, agent = agent_name, cat = cat_entry.basename, prefix = path_prefix)

                if cat_agent_names:
                    agent_categories.append(cat_entry.basename)
                    build_content += """
filegroup(
    name = "{plugin}_agents_{cat}",
    srcs = {members},
)
""".format(plugin = plugin_name, cat = cat_entry.basename, members = _label_list([plugin_name + "_" + n for n in cat_agent_names]))

        build_content += """
filegroup(
    name = "{plugin}_agents",
    srcs = {agents},
)
""".format(plugin = plugin_name, agents = _label_list([plugin_name + "_agents_" + c for c in agent_categories]))

        plugin_names.append(plugin_name)

    # Top-level aggregate filegroups across all embedded plugins.
    build_content += """
filegroup(
    name = "all_skills",
    srcs = {skills},
)

filegroup(
    name = "all_agents",
    srcs = {agents},
)
""".format(
        skills = _label_list([p + "_skills" for p in plugin_names]),
        agents = _label_list([p + "_agents" for p in plugin_names]),
    )

    ctx.file("BUILD.bazel", build_content)

claude_marketplace_repo = repository_rule(
    implementation = _claude_marketplace_repo_impl,
    attrs = dict(
        _GITHUB_ATTRS,
        sha256 = attr.string(mandatory = True),
        marketplace_json = attr.string(default = ".claude-plugin/marketplace.json", doc = "Path within the archive to the marketplace.json file."),
    ),
)

# --- Tag classes ---

def _tag_attrs(**extra):
    return dict(
        {"name": attr.string(mandatory = True, doc = "Repository name for use_repo() and @<name>//... references.")},
        **dict(_GITHUB_ATTRS, sha256 = attr.string(mandatory = True, doc = "SHA-256 checksum of the archive."), **extra)
    )

_gemini_extension_tag = tag_class(
    doc = "Declares an external Gemini extension repository.",
    attrs = _tag_attrs(),
)

_anthropics_skills_tag = tag_class(
    doc = "Declares an external agentskills.io-format skills repository.",
    attrs = _tag_attrs(),
)

_skill_collection_tag = tag_class(
    doc = "Declares an external skill collection (raw dirs with SKILL.md). :skills reflects include/exclude config; :all-skills is unfiltered.",
    attrs = _tag_attrs(
        namespace = attr.string(mandatory = True, doc = "Namespace prefix, e.g. 'gstack'."),
        include = attr.string_list(default = [], doc = "If non-empty, only these skill names appear in :skills."),
        exclude = attr.string_list(default = [], doc = "Skill names to omit from :skills."),
    ),
)

_claude_agents_tag = tag_class(
    doc = "Declares an external Claude sub-agents repository. Generates filegroups per division.",
    attrs = _tag_attrs(),
)

_claude_plugin_tag = tag_class(
    doc = "Declares an external Claude plugin repository (.claude-plugin/plugin.json). Use plugin_path for multi-plugin repos.",
    attrs = _tag_attrs(
        plugin_path = attr.string(default = "", doc = "Subpath to the plugin root within the archive. Empty = archive root."),
    ),
)

_claude_marketplace_tag = tag_class(
    doc = "Declares a Claude plugin marketplace archive (.claude-plugin/marketplace.json). Generates per-plugin filegroups for embedded plugins; external-source plugins must be declared separately via claude_plugin.",
    attrs = _tag_attrs(
        marketplace_json = attr.string(default = ".claude-plugin/marketplace.json", doc = "Path within the archive to the marketplace.json file."),
    ),
)

def _ai_skills_extension_impl(module_ctx):
    for mod in module_ctx.modules:
        for tag in mod.tags.gemini_extension:
            gemini_extension_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )
        for tag in mod.tags.anthropics_skills:
            anthropics_skills_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )
        for tag in mod.tags.skill_collection:
            skill_collection_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
                include = tag.include,
                exclude = tag.exclude,
            )
        for tag in mod.tags.claude_agents:
            claude_agents_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )
        for tag in mod.tags.claude_plugin:
            claude_plugin_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
                plugin_path = tag.plugin_path,
            )
        for tag in mod.tags.claude_marketplace:
            claude_marketplace_repo(
                name = tag.name,
                github = tag.github,
                tag = tag.tag,
                commit = tag.commit,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
                marketplace_json = tag.marketplace_json,
            )

ai_skills = module_extension(
    implementation = _ai_skills_extension_impl,
    tag_classes = {
        "gemini_extension": _gemini_extension_tag,
        "anthropics_skills": _anthropics_skills_tag,
        "skill_collection": _skill_collection_tag,
        "claude_agents": _claude_agents_tag,
        "claude_plugin": _claude_plugin_tag,
        "claude_marketplace": _claude_marketplace_tag,
    },
)
