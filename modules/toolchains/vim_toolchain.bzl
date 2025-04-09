"""Vim toolchain definition."""

load("//modules/toolchains:toolchain_types.bzl", "ToolInfo")

VimInfo = provider(
    doc = "Information about the Vim installation",
    fields = {
        "path": "Path to vim executable",
        "version": "Vim version string",
        "has_lua": "Boolean indicating if Vim has Lua support",
        "has_python": "Boolean indicating if Vim has Python support",
        "config_path": "Path to vim config directory",
    },
)

def _vim_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        vim_info = VimInfo(
            path = ctx.attr.path,
            version = ctx.attr.version,
            has_lua = ctx.attr.has_lua,
            has_python = ctx.attr.has_python,
            config_path = ctx.attr.config_path,
        ),
        tool_info = ToolInfo(
            name = "vim",
            path = ctx.attr.path,
            version = ctx.attr.version,
            available = ctx.attr.path != "",
            extra_info = {
                "has_lua": str(ctx.attr.has_lua),
                "has_python": str(ctx.attr.has_python),
                "config_path": ctx.attr.config_path,
            },
        ),
    )
    return [toolchain_info]

vim_toolchain = rule(
    implementation = _vim_toolchain_impl,
    attrs = {
        "path": attr.string(mandatory = True),
        "version": attr.string(default = ""),
        "has_lua": attr.bool(default = False),
        "has_python": attr.bool(default = False),
        "config_path": attr.string(default = ""),
    },
)

def _find_vim_tool_impl(ctx):
    vim_path = ""
    vim_version = ""
    has_lua = False
    has_python = False
    config_path = ""
    
    # Try to find vim executable
    result = ctx.execute(["which", "vim"])
    if result.return_code == 0:
        vim_path = result.stdout.strip()
        
        # Get vim version info
        version_result = ctx.execute([vim_path, "--version"])
        if version_result.return_code == 0:
            version_output = version_result.stdout
            
            # Extract version
            version_match = ctx.execute(["bash", "-c", "echo '{}' | grep -oE 'VIM - Vi IMproved ([0-9.]+)' | sed 's/VIM - Vi IMproved //'".format(version_output)])
            if version_match.return_code == 0 and version_match.stdout.strip():
                vim_version = version_match.stdout.strip()
                
            # Check for lua support
            has_lua = "+lua" in version_output
            
            # Check for python support
            has_python = "+python" in version_output or "+python3" in version_output
            
            # Try to find config path
            if ctx.os.name == "mac os x":
                config_path = "~/.vim"
            elif ctx.os.name.startswith("windows"):
                config_path = "$HOME/vimfiles"
            else:
                config_path = "~/.vim"
    
    # Write the build file that instantiates the toolchain
    ctx.file("BUILD.bazel", """
load("//modules/toolchains:vim_toolchain.bzl", "vim_toolchain")

package(default_visibility = ["//visibility:public"])

vim_toolchain(
    name = "vim_tool",
    path = "{}",
    version = "{}",
    has_lua = {},
    has_python = {},
    config_path = "{}",
)

toolchain(
    name = "vim_toolchain",
    toolchain = ":vim_tool",
    toolchain_type = "//:vim_toolchain_type",
)
""".format(vim_path, vim_version, "True" if has_lua else "False", 
           "True" if has_python else "False", config_path))

    # Write the helper for checking vim availability
    ctx.file("vim_info.bzl", """
def is_available():
    return {}

def get_path():
    return "{}"
    
def get_version():
    return "{}"

def has_lua():
    return {}
    
def has_python():
    return {}
""".format("True" if vim_path != "" else "False", vim_path, vim_version, 
           "True" if has_lua else "False", "True" if has_python else "False"))

find_vim_tool = repository_rule(
    implementation = _find_vim_tool_impl,
    attrs = {},
    local = True
)

# Vim toolchain type definition - moved to BUILD.bazel
def register_vim_toolchains():
    """Register the vim toolchain."""
    find_vim_tool(name = "vim_local_toolchain")
    
    native.register_toolchains(
        "@vim_local_toolchain//:vim_toolchain"
    )