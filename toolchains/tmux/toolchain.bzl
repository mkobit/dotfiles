"""
Toolchain rules for tmux.
"""

# Define the provider that will be used by rules needing access to tmux
TmuxInfo = provider(
    doc = "Information about how to invoke the tmux executable.",
    fields = {
        "tmux_path": "Path to the tmux executable",
        "tmux_version": "Version of tmux being used",
        "env": "Environment variables to set when invoking tmux",
    },
)

def _tmux_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        tmuxinfo = TmuxInfo(
            tmux_path = ctx.attr.tmux_path,
            tmux_version = ctx.attr.tmux_version,
            env = ctx.attr.env,
        ),
    )
    return [toolchain_info]

tmux_toolchain = rule(
    implementation = _tmux_toolchain_impl,
    attrs = {
        "tmux_path": attr.string(
            doc = "Path to the tmux executable",
            mandatory = True,
        ),
        "tmux_version": attr.string(
            doc = "Version of tmux being used",
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when invoking tmux",
            default = {},
        ),
    },
)

def _local_tmux_binary_impl(repository_ctx):
    # Find tmux binary in the path
    tmux_path = repository_ctx.which("tmux")
    if not tmux_path:
        fail("No tmux binary found in PATH")
    
    # Get tmux version
    result = repository_ctx.execute([tmux_path, "-V"])
    if result.return_code != 0:
        fail("Failed to determine tmux version: " + result.stderr)
    
    # Extract version from output format like "tmux 3.2a" 
    version_output = result.stdout.strip()
    version = version_output.split(" ")[1] if len(version_output.split(" ")) > 1 else "unknown"
    
    # Determine the current OS and CPU
    os = repository_ctx.os.name
    exec_constraints = []
    target_constraints = []
    
    # Set platform-specific constraints - make them broader to match host platform
    if os.startswith("mac"):
        # Use only OS constraint, don't restrict by CPU architecture
        exec_constraints = [
            "@platforms//os:macos",
        ]
        target_constraints = [
            "@platforms//os:macos",
        ]
    elif os.startswith("linux"):
        exec_constraints = [
            "@platforms//os:linux",
        ]
        target_constraints = [
            "@platforms//os:linux",
        ]
    else:
        # For any other OS, don't set constraints to make it more likely to match
        exec_constraints = []
        target_constraints = []
    
    # Format constraints for BUILD file
    exec_constraints_formatted = ""
    for c in exec_constraints:
        exec_constraints_formatted += '        "{}",\n'.format(c)
    
    target_constraints_formatted = ""
    for c in target_constraints:
        target_constraints_formatted += '        "{}",\n'.format(c)
    
    # Create the BUILD file with toolchain definition
    repository_ctx.file("BUILD.bazel", """
package(default_visibility = ["//visibility:public"])

# Define the toolchain implementation
load("@dotfiles//toolchains/tmux:toolchain.bzl", "tmux_toolchain")

tmux_toolchain(
    name = "tmux_local_impl",
    tmux_path = "{tmux_path}",
    tmux_version = "{version}",
)

# Declare the toolchain
toolchain(
    name = "tmux_local",
    exec_compatible_with = [
{exec_constraints}    ],
    target_compatible_with = [
{target_constraints}    ],
    toolchain = ":tmux_local_impl",
    toolchain_type = "@dotfiles//toolchains/tmux:toolchain_type",
)
""".format(
        tmux_path = tmux_path,
        version = version,
        exec_constraints = exec_constraints_formatted,
        target_constraints = target_constraints_formatted,
    ))

local_tmux_binary = repository_rule(
    implementation = _local_tmux_binary_impl,
    doc = "Creates a repository that contains a reference to the local tmux installation",
)