"""
Public API for ZSH rules.

This file provides the public interface for rules related to ZSH configuration.
"""

load(
    "//rules/zsh/private:zsh_config.bzl",
    _zsh_config = "zsh_config",
    _zsh_test = "zsh_test",
)

# Re-export rules with clean public API
zsh_config = _zsh_config
zsh_test = _zsh_test
