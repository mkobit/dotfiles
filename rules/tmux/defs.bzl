"""
Public API for tmux rules.
"""

load("//rules/tmux/private:tmux_conf_test.bzl", _tmux_conf_test = "tmux_conf_test")

# Re-export the rules
tmux_conf_test = _tmux_conf_test