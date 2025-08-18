"""
Public API for Vim rules.

This file provides the public interface for rules related to Vim configuration.
"""

load(
    "//rules/vim/private:vim_config.bzl",
    _vim_config = "vim_config",
    _vim_test = "vim_test",
)

# Re-export rules with clean public API
vim_config = _vim_config
vim_test = _vim_test
