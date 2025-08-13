"""
Rule for testing tmux configuration files.
"""

load("//rules/common:rule_utils.bzl", "create_config_test_rule")

# Define validation commands for tmux
_TMUX_VALIDATION_COMMANDS = [
    # Just validate the syntax without trying to start a server
    '"{tool_path}" -f "{config_path}" -L syntax_check new-session -d "true" 2>/dev/null || {{ echo "Failed to validate tmux configuration - syntax error"; exit 1; }}',
]

# Create the tmux configuration test rule using common utilities
tmux_conf_test = create_config_test_rule(
    rule_name = "tmux",
    toolchain_type = "//toolchains/tmux:toolchain_type",
    validation_commands = _TMUX_VALIDATION_COMMANDS,
    file_extensions = [".conf", ".tmux.conf"],
)
