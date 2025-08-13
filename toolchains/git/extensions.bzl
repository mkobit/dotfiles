"""
Module extension for git toolchain.
"""

load(":toolchain.bzl", "local_git_binary")

def _git_toolchain_impl(module_ctx):
    """Implementation of the git toolchain extension."""

    # Create a repository for the local git binary
    local_git_binary(name = "local_git")
    return module_ctx.extension_metadata(
        root_module_direct_deps = ["local_git"],
        root_module_direct_dev_deps = [],
    )

git_toolchain = module_extension(
    implementation = _git_toolchain_impl,
    doc = "Extension for git toolchain that discovers local git installation",
)
