"""
Module extension for zsh toolchain.
"""

load(":toolchain.bzl", "local_zsh_binary")

def _zsh_toolchain_impl(module_ctx):
    """Implementation of the zsh toolchain extension."""

    # Create a repository for the local zsh binary
    local_zsh_binary(name = "local_zsh")
    return module_ctx.extension_metadata(
        root_module_direct_deps = ["local_zsh"],
        root_module_direct_dev_deps = [],
    )

zsh_toolchain = module_extension(
    implementation = _zsh_toolchain_impl,
    doc = "Extension for zsh toolchain that discovers local zsh installation",
)
