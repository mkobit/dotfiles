"""
Module extension for declaring external AI skill repositories.

Usage in MODULE.bazel:

    ai_skills = use_extension("//tools/agentskills:extensions.bzl", "ai_skills")

    ai_skills.gemini_extension(
        name = "gemini_conductor",
        urls = ["https://..."],
        sha256 = "...",
        strip_prefix = "conductor-conductor-v0.4.1",
    )

    ai_skills.anthropics_skills(
        name = "anthropics_skills",
        urls = ["https://..."],
        sha256 = "...",
        strip_prefix = "skills-<commit>",
    )

    ai_skills.skill_collection(
        name = "gstack",
        namespace = "gstack",
        urls = ["https://..."],
        sha256 = "...",
        strip_prefix = "gstack-main",
    )

    ai_skills.claude_agents(
        name = "agency_agents",
        urls = ["https://..."],
        sha256 = "...",
        strip_prefix = "agency-agents-main",
    )

    use_repo(ai_skills, "anthropics_skills", "gemini_conductor", "gstack", "agency_agents")
"""

def _anthropics_skills_repo_impl(ctx):
    ctx.download_and_extract(
        url = ctx.attr.urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
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
    attrs = {
        "urls": attr.string_list(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(default = ""),
    },
)

def _gemini_extension_repo_impl(ctx):
    ctx.download_and_extract(
        url = ctx.attr.urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
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
    attrs = {
        "urls": attr.string_list(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(default = ""),
    },
)

def _skill_collection_repo_impl(ctx):
    ctx.download_and_extract(
        url = ctx.attr.urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
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
    attrs = {
        "urls": attr.string_list(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(default = ""),
        "include": attr.string_list(default = [], doc = "If non-empty, only these skill names appear in :skills."),
        "exclude": attr.string_list(default = [], doc = "Skill names to omit from :skills. Ignored when include is set."),
    },
)

def _claude_agents_repo_impl(ctx):
    ctx.download_and_extract(
        url = ctx.attr.urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
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
    attrs = {
        "urls": attr.string_list(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(default = ""),
    },
)

# --- Tag classes ---

_gemini_extension_tag = tag_class(
    doc = "Declares an external Gemini extension repository.",
    attrs = {
        "name": attr.string(mandatory = True, doc = "Repository name, used in use_repo() and as @<name>//:extension"),
        "urls": attr.string_list(mandatory = True, doc = "Download URLs for the extension archive"),
        "sha256": attr.string(mandatory = True, doc = "SHA-256 checksum of the archive"),
        "strip_prefix": attr.string(default = "", doc = "Path prefix to strip when extracting"),
    },
)

_anthropics_skills_tag = tag_class(
    doc = "Declares an external Anthropic-format skills repository (agentskills.io SKILL.md layout).",
    attrs = {
        "name": attr.string(mandatory = True, doc = "Repository name, used in use_repo()"),
        "urls": attr.string_list(mandatory = True, doc = "Download URLs for the skills archive"),
        "sha256": attr.string(mandatory = True, doc = "SHA-256 checksum of the archive"),
        "strip_prefix": attr.string(default = "", doc = "Path prefix to strip when extracting"),
    },
)

_skill_collection_tag = tag_class(
    doc = "Declares an external skill collection repository (e.g. gstack). Generates one filegroup per skill subdirectory. The :skills target reflects the configured selection; :all-skills is always unfiltered.",
    attrs = {
        "name": attr.string(mandatory = True, doc = "Repository name, used in use_repo()"),
        "urls": attr.string_list(mandatory = True, doc = "Download URLs for the collection archive"),
        "sha256": attr.string(mandatory = True, doc = "SHA-256 checksum of the archive"),
        "strip_prefix": attr.string(default = "", doc = "Path prefix to strip when extracting"),
        "namespace": attr.string(mandatory = True, doc = "Namespace prefix, e.g. 'gstack'"),
        "include": attr.string_list(default = [], doc = "If non-empty, only these skill names appear in :skills. Takes precedence over exclude."),
        "exclude": attr.string_list(default = [], doc = "Skill names to omit from :skills. Ignored when include is set."),
    },
)

_claude_agents_tag = tag_class(
    doc = "Declares an external Claude sub-agents repository. Generates filegroups per division and per individual agent.",
    attrs = {
        "name": attr.string(mandatory = True, doc = "Repository name, used in use_repo()"),
        "urls": attr.string_list(mandatory = True, doc = "Download URLs for the agents archive"),
        "sha256": attr.string(mandatory = True, doc = "SHA-256 checksum of the archive"),
        "strip_prefix": attr.string(default = "", doc = "Path prefix to strip when extracting"),
        "divisions": attr.string_list(default = [], doc = "Divisions to include (empty = all)"),
    },
)

def _ai_skills_extension_impl(module_ctx):
    for mod in module_ctx.modules:
        for tag in mod.tags.gemini_extension:
            gemini_extension_repo(
                name = tag.name,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )
        for tag in mod.tags.anthropics_skills:
            anthropics_skills_repo(
                name = tag.name,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )
        for tag in mod.tags.skill_collection:
            skill_collection_repo(
                name = tag.name,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
                include = tag.include,
                exclude = tag.exclude,
            )
        for tag in mod.tags.claude_agents:
            claude_agents_repo(
                name = tag.name,
                urls = tag.urls,
                sha256 = tag.sha256,
                strip_prefix = tag.strip_prefix,
            )

ai_skills = module_extension(
    implementation = _ai_skills_extension_impl,
    tag_classes = {
        "gemini_extension": _gemini_extension_tag,
        "anthropics_skills": _anthropics_skills_tag,
        "skill_collection": _skill_collection_tag,
        "claude_agents": _claude_agents_tag,
    },
)
