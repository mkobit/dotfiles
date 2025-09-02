"""
Public API for JSON merge and patch rules.

This module provides rules for merging JSON files and applying JSON patches,
following RFC 6902 for deterministic JSON transformations.
"""

load("//rules/json_merge/private:json_merge.bzl", _json_merge = "json_merge", _json_patch = "json_patch")

# Re-export public rules
json_merge = _json_merge
json_patch = _json_patch
