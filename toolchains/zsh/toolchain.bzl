"""
Toolchain rules for zsh.
"""

load("//toolchains/common:toolchain_utils.bzl", "create_tool_info_provider", "create_toolchain_rule", "create_local_tool_repository_rule")

# Create the provider and toolchain rule using common utilities
ZshInfo = create_tool_info_provider("zsh")
zsh_toolchain = create_toolchain_rule("zsh", ZshInfo)

# Create the repository rule for local zsh discovery
local_zsh_binary = create_local_tool_repository_rule("zsh")
