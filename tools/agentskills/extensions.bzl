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

    use_repo(ai_skills, "anthropics_skills", "gemini_conductor")
"""

def _anthropics_skills_repo_impl(ctx):
    ctx.download_and_extract(
        url = ctx.attr.urls,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
    )

    build_content = """load("@//tools/agentskills:rules.bzl", "agent_skill")

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

    build_content = """load("@//tools/agentskills:rules.bzl", "gemini_extension")

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

ai_skills = module_extension(
    implementation = _ai_skills_extension_impl,
    tag_classes = {
        "gemini_extension": _gemini_extension_tag,
        "anthropics_skills": _anthropics_skills_tag,
    },
)
