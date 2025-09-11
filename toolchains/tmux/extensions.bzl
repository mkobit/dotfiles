"""Module extensions for tmux toolchain."""

load("//toolchains/tmux:toolchain.bzl", "tmux_repository")

def _tmux_toolchain_extension_impl(mctx):
    # Create a repository that provides all tmux variants
    tmux_repository(name = "tmux")

    # Return None, which is valid for module extensions
    return None

# Define the module extension
tmux_toolchain = module_extension(
    implementation = _tmux_toolchain_extension_impl,
    doc = """
    An extension that provides all tmux toolchain variants under @tmux.
    
    Example usage:
    ```starlark
    tmux_ext = use_extension("//toolchains/tmux:extensions.bzl", "tmux_toolchain")
    use_repo(tmux_ext, "tmux")
    register_toolchains("@tmux//:local", "@tmux//:linux_amd64")
    ```
    """,
)
