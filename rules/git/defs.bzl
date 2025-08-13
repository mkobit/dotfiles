"""
Public API for Git rules.

This file provides the public interface for rules related to Git configuration.
"""

load(
    "//rules/git/private:git_config.bzl",
    _git_config = "git_config",
    _git_test = "git_test",
)

# Re-export rules with clean public API
git_config = _git_config
git_test = _git_test
