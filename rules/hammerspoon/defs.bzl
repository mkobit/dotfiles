"""
Public API for Hammerspoon rules.

This file provides the public interface for rules related to Hammerspoon configuration.
"""

load(
    "//rules/hammerspoon/private:hammerspoon_config.bzl",
    _hammerspoon_config = "hammerspoon_config",
    _hammerspoon_test = "hammerspoon_test",
)

# Re-export rules with clean public API
hammerspoon_config = _hammerspoon_config
hammerspoon_test = _hammerspoon_test