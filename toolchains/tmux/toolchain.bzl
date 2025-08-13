"""
Toolchain rules for tmux.
"""

load("//toolchains/common:toolchain_utils.bzl", "create_local_tool_repository_rule", "create_tool_info_provider", "create_toolchain_rule")

# Create the provider and toolchain rule using common utilities
TmuxInfo = create_tool_info_provider("tmux")
tmux_toolchain = create_toolchain_rule("tmux", TmuxInfo)

# Create the repository rule for local tmux discovery
local_tmux_binary = create_local_tool_repository_rule("tmux")
