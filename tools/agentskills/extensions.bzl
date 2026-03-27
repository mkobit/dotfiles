load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

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

def _ai_skills_extension_impl(module_ctx):
    # This extension currently hardcodes the repositories we want to pull.
    # We could easily expose tags to make this dynamic in the future.
    anthropics_skills_repo(
        name = "anthropics_skills",
        urls = ["https://github.com/anthropics/skills/archive/98669c11ca63e9c81c11501e1437e5c47b556621.tar.gz"],
        sha256 = "435b687005b44bbc70c1c95e4362532987fe06547f6740ceba05fbdcc200aac3",
        strip_prefix = "skills-98669c11ca63e9c81c11501e1437e5c47b556621",
    )

    gemini_extension_repo(
        name = "gemini_conductor",
        urls = ["https://github.com/gemini-cli-extensions/conductor/archive/refs/tags/conductor-v0.4.1.tar.gz"],
        sha256 = "701f09ab6a2f13edf384ef6171d79b67e4b4692d3fa2a81035a6b72439129d1a",
        strip_prefix = "conductor-conductor-v0.4.1",
    )

ai_skills = module_extension(
    implementation = _ai_skills_extension_impl,
)
