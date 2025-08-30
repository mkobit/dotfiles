"""
Public API for JSON patch rules.

This module provides rules for applying JSON patches to files,
following RFC 6902 for deterministic JSON transformations.
"""

load("//rules/json_merge/private:json_merge.bzl", _json_patch = "json_patch")

# Re-export public rules
json_patch = _json_patch
