load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("//tools/tmux/private:repo_rules.bzl", "tmux_hub")
load("//tools/tmux/private:versions.bzl", "TMUX_VERSIONS")

_toolchain_tag = tag_class(
    attrs = {
        "version": attr.string(
            mandatory = True,
            doc = "The version of tmux to use. Available versions: " + ", ".join(TMUX_VERSIONS.keys()),
        ),
    },
)

def _tmux_extension_impl(module_ctx):
    # Find the requested version.
    # A single version must be determined across the entire build.
    # The root module takes precedence.
    version = None
    for mod in module_ctx.modules:
        for tag in mod.tags.toolchain:
            if mod.is_root:
                version = tag.version
            elif not version:
                version = tag.version

    if not version:
        fail("No tmux toolchain version requested. Use `tmux.toolchain(version = '...')` in MODULE.bazel")

    if version not in TMUX_VERSIONS:
        fail("Unsupported tmux version: {}. Available versions are: {}".format(
            version,
            ", ".join(TMUX_VERSIONS.keys()),
        ))

    platforms_info = TMUX_VERSIONS[version]

    # 1. Instantiate platform-specific http_archives
    for platform_key, info in platforms_info.items():
        repo_name = "tmux_{}".format(platform_key)

        # We assume they all provide a file called `tmux` in their root after extraction/download.
        build_content = """
exports_files(["tmux"])
"""
        http_archive(
            name = repo_name,
            urls = [info["url"]],
            sha256 = info["sha256"],
            strip_prefix = info.get("strip_prefix", ""),
            build_file_content = build_content,
            type = "tar.gz",
        )

    # 2. Instantiate the hub repository
    tmux_hub(
        name = "tmux",
    )

tmux = module_extension(
    implementation = _tmux_extension_impl,
    tag_classes = {"toolchain": _toolchain_tag},
    doc = "Extension for downloading and setting up tmux.",
)
