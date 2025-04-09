"""Homebrew (brew) toolchain definition."""

load("//modules/toolchains:toolchain_types.bzl", "ToolInfo")

BrewInfo = provider(
    doc = "Information about the Homebrew installation",
    fields = {
        "path": "Path to brew executable",
        "version": "Brew version string",
        "prefix": "Homebrew installation prefix",
        "cellar": "Homebrew Cellar directory",
    },
)

def _brew_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        brew_info = BrewInfo(
            path = ctx.attr.path,
            version = ctx.attr.version,
            prefix = ctx.attr.prefix,
            cellar = ctx.attr.cellar,
        ),
        tool_info = ToolInfo(
            name = "brew",
            path = ctx.attr.path,
            version = ctx.attr.version,
            available = ctx.attr.path != "",
            extra_info = {
                "prefix": ctx.attr.prefix,
                "cellar": ctx.attr.cellar,
            },
        ),
    )
    return [toolchain_info]

brew_toolchain = rule(
    implementation = _brew_toolchain_impl,
    attrs = {
        "path": attr.string(mandatory = True),
        "version": attr.string(default = ""),
        "prefix": attr.string(default = ""),
        "cellar": attr.string(default = ""),
    },
)

def _find_brew_tool_impl(ctx):
    brew_path = ""
    brew_version = ""
    brew_prefix = ""
    brew_cellar = ""
    
    # Try to find brew executable
    result = ctx.execute(["which", "brew"])
    if result.return_code == 0:
        brew_path = result.stdout.strip()
        
        # Get brew version info
        version_result = ctx.execute([brew_path, "--version"])
        if version_result.return_code == 0:
            version_output = version_result.stdout
            
            # Extract version
            version_match = ctx.execute(["bash", "-c", "echo '{}' | grep -oE 'Homebrew ([0-9.]+)' | sed 's/Homebrew //'".format(version_output)])
            if version_match.return_code == 0 and version_match.stdout.strip():
                brew_version = version_match.stdout.strip()
        
        # Get brew prefix
        prefix_result = ctx.execute([brew_path, "--prefix"])
        if prefix_result.return_code == 0:
            brew_prefix = prefix_result.stdout.strip()
            
            # Cellar is typically under prefix
            brew_cellar = brew_prefix + "/Cellar"
    
    # Write the build file that instantiates the toolchain
    ctx.file("BUILD.bazel", """
load("//modules/toolchains:brew_toolchain.bzl", "brew_toolchain")

package(default_visibility = ["//visibility:public"])

brew_toolchain(
    name = "brew_tool",
    path = "{}",
    version = "{}",
    prefix = "{}",
    cellar = "{}",
)

toolchain(
    name = "brew_toolchain",
    toolchain = ":brew_tool",
    toolchain_type = "//:brew_toolchain_type",
)
""".format(brew_path, brew_version, brew_prefix, brew_cellar))

    # Write the helper for checking brew availability and paths
    ctx.file("brew_info.bzl", """
def is_available():
    return {}

def get_path():
    return "{}"
    
def get_version():
    return "{}"
    
def get_prefix():
    return "{}"
    
def get_cellar():
    return "{}"
""".format(brew_path != "", brew_path, brew_version, brew_prefix, brew_cellar))

find_brew_tool = repository_rule(
    implementation = _find_brew_tool_impl,
    attrs = {},
    local = True
)

# Brew toolchain type definition - moved to BUILD.bazel
def register_brew_toolchains():
    """Register the brew toolchain."""
    find_brew_tool(name = "brew_local_toolchain")
    
    native.register_toolchains(
        "@brew_local_toolchain//:brew_toolchain"
    )