def _ruff_hub_impl(repository_ctx):
    # This repository acts as a simple router that provides a stable target (`@ruff//:ruff`)
    # that uses Bazel's platform-specific mechanisms to point to the correct dynamically
    # downloaded static binary repository (e.g., `@ruff_x86_64_unknown_linux_gnu`).

    build_content = """
package(default_visibility = ["//visibility:public"])

alias(
    name = "ruff",
    actual = select({
        "@bazel_tools//src/conditions:linux_x86_64": "@ruff_x86_64_unknown_linux_gnu//:ruff",
        "@bazel_tools//src/conditions:linux_aarch64": "@ruff_aarch64_unknown_linux_gnu//:ruff",
        "@bazel_tools//src/conditions:darwin_x86_64": "@ruff_x86_64_apple_darwin//:ruff",
        "@bazel_tools//src/conditions:darwin_arm64": "@ruff_aarch64_apple_darwin//:ruff",
    }),
)
"""
    repository_ctx.file("BUILD.bazel", build_content)

ruff_hub = repository_rule(
    implementation = _ruff_hub_impl,
)
