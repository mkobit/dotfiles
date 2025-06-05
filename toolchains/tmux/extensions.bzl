"""Module extensions for tmux toolchain."""

load("//toolchains/tmux:toolchain.bzl", "local_tmux_binary")

def _tmux_toolchain_extension_impl(mctx):
    # Create a repository for the local tmux binary
    local_tmux_binary(name = "local_tmux")
    
    # Return None, which is valid for module extensions
    return None

# Define the module extension
tmux_toolchain = module_extension(
    implementation = _tmux_toolchain_extension_impl,
    doc = """
    An extension that locates the local tmux installation.
    The toolchain needs to be registered separately with register_toolchains.
    
    Example usage:
    ```starlark
    tmux_ext = use_extension("//toolchains/tmux:extensions.bzl", "tmux_toolchain")
    use_repo(tmux_ext, "local_tmux")
    register_toolchains("@local_tmux//:tmux_local")
    ```
    """
)