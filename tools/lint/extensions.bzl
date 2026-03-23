load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("//tools/lint/private:repo_rules.bzl", "ruff_hub")
load("//tools/lint/private:versions.bzl", "RUFF_VERSIONS")

_toolchain_tag = tag_class(
    attrs = {
        "version": attr.string(
            mandatory = True,
            doc = "The version of ruff to use. Available versions: " + ", ".join(RUFF_VERSIONS.keys()),
        ),
    },
)

def _ruff_extension_impl(module_ctx):
    version = None
    for mod in module_ctx.modules:
        for tag in mod.tags.toolchain:
            if mod.is_root:
                version = tag.version
            elif not version:
                version = tag.version

    if not version:
        fail("No ruff toolchain version requested. Use `ruff.toolchain(version = '...')` in MODULE.bazel")

    if version not in RUFF_VERSIONS:
        fail("Unsupported ruff version: {}. Available versions are: {}".format(
            version,
            ", ".join(RUFF_VERSIONS.keys()),
        ))

    platforms_info = RUFF_VERSIONS[version]

    for platform_key, info in platforms_info.items():
        repo_name = "ruff_{}".format(platform_key)

        build_content = """
exports_files(["ruff"])
"""
        http_archive(
            name = repo_name,
            urls = info["urls"],
            sha256 = info["sha256"],
            strip_prefix = info.get("strip_prefix", ""),
            build_file_content = build_content,
            type = "tar.gz",
        )

    ruff_hub(
        name = "ruff",
    )

ruff = module_extension(
    implementation = _ruff_extension_impl,
    tag_classes = {"toolchain": _toolchain_tag},
    doc = "Extension for downloading and setting up ruff.",
)
