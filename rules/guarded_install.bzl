"""
Public API for guarded installation rules.

This file provides the public interface for rules that can safely inject
configuration content into existing files using guard comments.
"""

load(
    "//rules/common:guarded_install.bzl",
    _guarded_install_rule = "guarded_install_rule",
)

# Re-export rule with clean public API
guarded_install = _guarded_install_rule
