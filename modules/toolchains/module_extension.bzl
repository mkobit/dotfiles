"""Module extension to register toolchains."""

load("//modules/toolchains:vim_toolchain.bzl", "find_vim_tool")
load("//modules/toolchains:neovim_toolchain.bzl", "find_neovim_tool")
load("//modules/toolchains:brew_toolchain.bzl", "find_brew_tool")

def _toolchains_extension_impl(mctx):
    # Register repo rules for each toolchain
    find_vim_tool(name = "vim_local_toolchain")
    find_neovim_tool(name = "neovim_local_toolchain")
    find_brew_tool(name = "brew_local_toolchain")
    
    # Register the toolchains
    mctx.register_toolchains(
        "@vim_local_toolchain//:vim_toolchain",
        "@neovim_local_toolchain//:neovim_toolchain",
        "@brew_local_toolchain//:brew_toolchain",
    )

# Define the extension
toolchains_extension = module_extension(
    implementation = _toolchains_extension_impl,
)