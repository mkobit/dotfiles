"""
Public API for JSON merge rules.

This module provides rules for merging JSON files with configurable strategies,
following the dotfiles repository patterns for deterministic configuration management.
"""

load("//rules/json_merge/private:json_merge.bzl", _json_merge = "json_merge")

# Re-export public rules
json_merge = _json_merge
