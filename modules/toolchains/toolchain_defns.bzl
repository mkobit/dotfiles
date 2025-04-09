"""Toolchain definitions for common tools."""

# Provider definitions
VimInfo = provider(
    doc = "Information about the vim toolchain",
    fields = {
        "path": "Path to the vim executable",
    },
)

NeovimInfo = provider(
    doc = "Information about the neovim toolchain",
    fields = {
        "path": "Path to the neovim executable",
    },
)

BrewInfo = provider(
    doc = "Information about the homebrew toolchain",
    fields = {
        "path": "Path to the brew executable",
    },
)

# Vim toolchain implementation
def _vim_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        vim_info = VimInfo(
            path = ctx.attr.path,
        ),
    )
    return [toolchain_info]

vim_toolchain = rule(
    implementation = _vim_toolchain_impl,
    attrs = {
        "path": attr.string(
            doc = "Path to the vim executable",
            default = "vim",
        ),
    },
)

# Neovim toolchain implementation
def _neovim_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        neovim_info = NeovimInfo(
            path = ctx.attr.path,
        ),
    )
    return [toolchain_info]

neovim_toolchain = rule(
    implementation = _neovim_toolchain_impl,
    attrs = {
        "path": attr.string(
            doc = "Path to the neovim executable",
            default = "nvim",
        ),
    },
)

# Brew toolchain implementation
def _brew_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        brew_info = BrewInfo(
            path = ctx.attr.path,
        ),
    )
    return [toolchain_info]

brew_toolchain = rule(
    implementation = _brew_toolchain_impl,
    attrs = {
        "path": attr.string(
            doc = "Path to the brew executable",
            default = "brew",
        ),
    },
)