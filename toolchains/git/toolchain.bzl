"""
Toolchain rules for git.
"""

load("//toolchains/common:toolchain_utils.bzl", "create_local_tool_repository_rule", "create_tool_info_provider", "create_toolchain_rule")

# Create the provider and toolchain rule using common utilities
GitInfo = create_tool_info_provider("git")
git_toolchain = create_toolchain_rule("git", GitInfo)

# Create the repository rule for local git discovery
# Git uses --version instead of -V for version info
local_git_binary = create_local_tool_repository_rule("git", version_flag = "--version")
