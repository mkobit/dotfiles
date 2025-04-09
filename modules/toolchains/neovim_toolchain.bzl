"""Neovim toolchain definition."""

load("//modules/toolchains:toolchain_types.bzl", "ToolInfo")

NeovimInfo = provider(
    doc = "Information about the Neovim installation",
    fields = {
        "path": "Path to neovim executable",
        "version": "Neovim version string",
        "config_path": "Path to neovim config directory",
        "runtime_path": "Path to neovim runtime directory",
    },
)

def _neovim_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        neovim_info = NeovimInfo(
            path = ctx.attr.path,
            version = ctx.attr.version,
            config_path = ctx.attr.config_path,
            runtime_path = ctx.attr.runtime_path,
        ),
        tool_info = ToolInfo(
            name = "neovim",
            path = ctx.attr.path,
            version = ctx.attr.version,
            available = ctx.attr.path != "",
            extra_info = {
                "config_path": ctx.attr.config_path,
                "runtime_path": ctx.attr.runtime_path,
            },
        ),
    )
    return [toolchain_info]

neovim_toolchain = rule(
    implementation = _neovim_toolchain_impl,
    attrs = {
        "path": attr.string(mandatory = True),
        "version": attr.string(default = ""),
        "config_path": attr.string(default = ""),
        "runtime_path": attr.string(default = ""),
    },
)

def _find_neovim_tool_impl(ctx):
    nvim_path = ""
    nvim_version = ""
    config_path = ""
    runtime_path = ""
    
    # Try to find neovim executable (check both nvim and neovim)
    for exe in ["nvim", "neovim"]:
        result = ctx.execute(["which", exe])
        if result.return_code == 0:
            nvim_path = result.stdout.strip()
            break
    
    if nvim_path:
        # Get neovim version info
        version_result = ctx.execute([nvim_path, "--version"])
        if version_result.return_code == 0:
            version_output = version_result.stdout
            
            # Extract version
            version_match = ctx.execute(["bash", "-c", "echo '{}' | grep -oE 'NVIM v([0-9.]+)' | sed 's/NVIM v//'".format(version_output)])
            if version_match.return_code == 0 and version_match.stdout.strip():
                nvim_version = version_match.stdout.strip()
        
        # Determine config path based on OS
        if ctx.os.name == "mac os x" or ctx.os.name.startswith("linux"):
            config_path = "~/.config/nvim"
            runtime_path = "/usr/share/nvim/runtime"
            
            # Check if XDG_CONFIG_HOME is set
            env_result = ctx.execute(["sh", "-c", "echo $XDG_CONFIG_HOME"])
            if env_result.return_code == 0 and env_result.stdout.strip():
                config_path = env_result.stdout.strip() + "/nvim"
        elif ctx.os.name.startswith("windows"):
            config_path = "$LOCALAPPDATA/nvim"
            runtime_path = "$LOCALAPPDATA/nvim-data/runtime"
    
    # Write the build file that instantiates the toolchain
    ctx.file("BUILD.bazel", """
load("//modules/toolchains:neovim_toolchain.bzl", "neovim_toolchain")

package(default_visibility = ["//visibility:public"])

neovim_toolchain(
    name = "neovim_tool",
    path = "{}",
    version = "{}",
    config_path = "{}",
    runtime_path = "{}",
)

toolchain(
    name = "neovim_toolchain",
    toolchain = ":neovim_tool",
    toolchain_type = "//:neovim_toolchain_type",
)
""".format(nvim_path, nvim_version, config_path, runtime_path))

    # Write the helper for checking neovim availability
    ctx.file("neovim_info.bzl", """
def is_available():
    return {}

def get_path():
    return "{}"
    
def get_version():
    return "{}"
    
def get_config_path():
    return "{}"
""".format("True" if nvim_path != "" else "False", nvim_path, nvim_version, config_path))

find_neovim_tool = repository_rule(
    implementation = _find_neovim_tool_impl,
    attrs = {},
    local = True
)

# Neovim toolchain type definition - moved to BUILD.bazel
def register_neovim_toolchains():
    """Register the neovim toolchain."""
    find_neovim_tool(name = "neovim_local_toolchain")
    
    native.register_toolchains(
        "@neovim_local_toolchain//:neovim_toolchain"
    )