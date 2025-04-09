"""Toolchain registration and utilities."""

load("//modules/toolchains:vim_toolchain.bzl", "find_vim_tool")
load("//modules/toolchains:neovim_toolchain.bzl", "find_neovim_tool")
load("//modules/toolchains:brew_toolchain.bzl", "find_brew_tool")

def register_all_toolchains():
    """Register all toolchains."""
    # We don't define toolchain types here, as they are defined in BUILD.bazel
    # Just register repository rules to find local toolchains
    find_vim_tool(name = "vim_local_toolchain")
    find_neovim_tool(name = "neovim_local_toolchain")
    find_brew_tool(name = "brew_local_toolchain")
    
    # Register the toolchains
    native.register_toolchains(
        "@vim_local_toolchain//:vim_toolchain",
        "@neovim_local_toolchain//:neovim_toolchain",
        "@brew_local_toolchain//:brew_toolchain"
    )