"""
Public API for JSON merge and patch rules.

This module provides rules for merging JSON files and applying JSON patches,
following RFC 6902 for deterministic JSON transformations.
"""

load("//rules/json_merge/private:json_merge.bzl", _json_add = "json_add", _json_merge = "json_merge", _json_patch = "json_patch", _json_remove = "json_remove", _json_replace = "json_replace")

# Re-export public rules
json_merge = _json_merge
json_patch = _json_patch
json_add = _json_add
json_replace = _json_replace
json_remove = _json_remove
