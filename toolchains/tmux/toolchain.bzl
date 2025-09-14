"""
Toolchain rules for tmux.
"""

load("//toolchains/common:toolchain_utils.bzl", "create_tool_info_provider", "create_toolchain_rule")

# Create the provider and toolchain rule using common utilities
TmuxInfo = create_tool_info_provider("tmux")
tmux_toolchain = create_toolchain_rule("tmux", TmuxInfo)

def _tmux_repository_impl(repository_ctx):
    """Repository rule that provides all tmux variants under @tmux."""

    # Try to find local tmux first
    local_tmux_path = repository_ctx.which("tmux")
    local_version = "unknown"

    if local_tmux_path:
        # Get version from local tmux binary
        result = repository_ctx.execute([local_tmux_path, "-V"])
        if result.return_code == 0:
            version_output = result.stdout.strip()
            parts = version_output.split(" ")
            local_version = parts[1] if len(parts) > 1 else "unknown"

    # Determine platform and fallback binary
    os = repository_ctx.os.name
    arch = repository_ctx.os.arch

    # Platform constraints for current environment
    exec_constraints = []
    target_constraints = []
    fallback_target = "linux_amd64"  # default fallback

    if os.startswith("mac"):
        exec_constraints = ["@platforms//os:macos"]
        target_constraints = ["@platforms//os:macos"]
        fallback_target = "linux_amd64"  # Could add macos binaries later
    elif os.startswith("linux"):
        exec_constraints = ["@platforms//os:linux"]
        target_constraints = ["@platforms//os:linux"]
        if arch == "aarch64" or arch == "arm64":
            fallback_target = "linux_arm64"
        else:
            fallback_target = "linux_amd64"

    # Format constraints for BUILD file
    exec_constraints_formatted = ""
    for c in exec_constraints:
        exec_constraints_formatted += '        "{}",\n'.format(c)

    target_constraints_formatted = ""
    for c in target_constraints:
        target_constraints_formatted += '        "{}",\n'.format(c)

    # Create BUILD file content
    build_content = '''
package(default_visibility = ["//visibility:public"])

load("@dotfiles//toolchains/tmux:toolchain.bzl", "tmux_toolchain")
'''

    # Always create a local toolchain - use system tmux if available, otherwise fallback
    if local_tmux_path:
        tmux_path = local_tmux_path
        tmux_version = local_version
    else:
        # Use the appropriate platform fallback
        tmux_path = "@tmux_{}//:tmux".format(fallback_target)
        tmux_version = "3.5a"  # Version of downloaded binaries

    build_content += '''
# Local tmux toolchain (system tmux or platform-appropriate fallback)
tmux_toolchain(
    name = "local_impl",
    tmux_path = "{tmux_path}",
    tmux_version = "{tmux_version}",
)

toolchain(
    name = "local",
    exec_compatible_with = [
{exec_constraints}    ],
    target_compatible_with = [
{target_constraints}    ],
    toolchain = ":local_impl",
    toolchain_type = "@dotfiles//toolchains/tmux:toolchain_type",
)
'''.format(
        tmux_path = tmux_path,
        tmux_version = tmux_version,
        exec_constraints = exec_constraints_formatted,
        target_constraints = target_constraints_formatted,
    )

    # Add downloaded static binary toolchains
    build_content += '''
# Downloaded static binaries (fallback)
tmux_toolchain(
    name = "linux_amd64_impl",
    tmux_path = "@tmux_linux_amd64//:tmux",
    tmux_version = "3.5a",
)

toolchain(
    name = "linux_amd64",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":linux_amd64_impl",
    toolchain_type = "@dotfiles//toolchains/tmux:toolchain_type",
)

tmux_toolchain(
    name = "linux_arm64_impl",
    tmux_path = "@tmux_linux_arm64//:tmux",
    tmux_version = "3.5a",
)

toolchain(
    name = "linux_arm64",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:arm64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:arm64",
    ],
    toolchain = ":linux_arm64_impl",
    toolchain_type = "@dotfiles//toolchains/tmux:toolchain_type",
)
'''

    repository_ctx.file("BUILD.bazel", build_content)

# Create the repository rule for tmux variants
tmux_repository = repository_rule(
    implementation = _tmux_repository_impl,
    doc = "Creates a repository that provides all tmux toolchain variants",
)
