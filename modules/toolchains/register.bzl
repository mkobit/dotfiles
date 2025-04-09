"""Register default toolchains."""

def register_default_toolchains():
    """Register default toolchains for the module."""
    native.register_toolchains(
        "//platforms/common:default_vim_toolchain",
        "//platforms/common:default_neovim_toolchain",
        "//platforms/common:default_brew_toolchain",
    )