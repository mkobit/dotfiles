"""
Public API for include-based installation rules.
"""

load("//rules/common:include_install.bzl", _include_install = "include_install")

# Re-export the include_install function
include_install = _include_install
