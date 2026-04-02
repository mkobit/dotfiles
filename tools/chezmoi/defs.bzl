"""Public deployment tag constants for chezmoi-managed AI tool targets.

These constants are referenced by Bazel macros (tools/agentskills/) and
chezmoi templates (src/chezmoi/) to coordinate installation and removal.
Keeping them here rather than in tools/agentskills/ makes the deployment
semantics explicit: these tags have no build meaning, only deployment meaning.

Usage in macros:
    load("//tools/chezmoi:defs.bzl", "CHEZMOI_SKIP_INSTALL", "CHEZMOI_TOMBSTONE")

Usage in chezmoi cquery (install — exclude both):
    attr(tags, "tool:claude", //...) except attr(tags, "tombstone", //...) except attr(tags, "skip-install", //...)

Usage in chezmoi cquery (remove):
    attr(tags, "tool:claude", //...) intersect attr(tags, "tombstone", //...)
"""

# Applied to targets that should be deleted from their deployment destination
# on the next chezmoi apply. Use with any tool:* tag.
# Boolean AND with the tool tag in cquery finds targets to remove:
#   attr(tags, "tool:claude", //...) intersect attr(tags, "tombstone", //...)
CHEZMOI_TOMBSTONE = "tombstone"

# Applied to test fixture targets that exist in the build graph but must never
# be installed by chezmoi. Prevents test skill targets from appearing in
# chezmoi externals queries.
CHEZMOI_SKIP_INSTALL = "skip-install"
