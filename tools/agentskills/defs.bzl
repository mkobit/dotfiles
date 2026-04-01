"""
Public API for agentskills Bazel rules.

Load from this file, not from private/ subpackage:

    load("//tools/agentskills:defs.bzl",
        "agent_skill",
        "claude_skill",
        "gemini_skill",
        "cursor_skill",
        "claude_from_gemini_extension",
        "gemini_extension",
        "claude_skill_group",
        "claude_skill_item",
        "claude_subagent_group",
        "claude_subagent",
    )
"""

load(
    "//tools/agentskills/private:collection.bzl",
    _claude_skill_group = "claude_skill_group",
    _claude_skill_item = "claude_skill_item",
    _claude_subagent = "claude_subagent",
    _claude_subagent_group = "claude_subagent_group",
)
load(
    "//tools/agentskills/private:gemini.bzl",
    _claude_from_gemini_extension = "claude_from_gemini_extension",
    _gemini_extension = "gemini_extension",
)
load(
    "//tools/agentskills/private:skill.bzl",
    _agent_skill = "agent_skill",
    _claude_skill = "claude_skill",
    _cursor_skill = "cursor_skill",
    _gemini_skill = "gemini_skill",
)

agent_skill = _agent_skill
claude_skill = _claude_skill
gemini_skill = _gemini_skill
cursor_skill = _cursor_skill
gemini_extension = _gemini_extension
claude_from_gemini_extension = _claude_from_gemini_extension
claude_skill_group = _claude_skill_group
claude_skill_item = _claude_skill_item
claude_subagent_group = _claude_subagent_group
claude_subagent = _claude_subagent
