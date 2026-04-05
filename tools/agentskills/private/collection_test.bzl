"""Analysis tests for collection.bzl packaging macros.

Verifies that each macro:
  - propagates the correct tags to the filegroup wrapper, and
  - produces an output archive with the expected filename suffix.
"""

load("@rules_testing//lib:analysis_test.bzl", "analysis_test", "test_suite")
load("@rules_testing//lib:truth.bzl", "matching")
load(
    ":collection.bzl",
    "claude_plugin_commands",
    "claude_skill_group",
    "claude_subagent",
    "claude_subagent_group",
    "cursor_skill_group",
    "gemini_skill_group",
)

# --------------------------------------------------------------------------- #
# claude_skill_group
# --------------------------------------------------------------------------- #

def _test_claude_skill_group_tags(name):
    claude_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-ns",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _claude_skill_group_tags_impl,
    )

def _claude_skill_group_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:claude",
        "claude:collection",
        "skill-group:test-ns",
    ])

def _test_claude_skill_group_output(name):
    claude_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-ns",
        install_name = "my-install",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _claude_skill_group_output_impl,
    )

def _claude_skill_group_output_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("my-install.claude.skill-group.tar"),
    )

def _test_claude_skill_group_namespace_default(name):
    """install_name defaults to namespace when omitted."""
    claude_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "ns-default",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _claude_skill_group_namespace_default_impl,
    )

def _claude_skill_group_namespace_default_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("ns-default.claude.skill-group.tar"),
    )

# --------------------------------------------------------------------------- #
# gemini_skill_group
# --------------------------------------------------------------------------- #

def _test_gemini_skill_group_tags(name):
    gemini_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-gemini-ns",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _gemini_skill_group_tags_impl,
    )

def _gemini_skill_group_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:gemini",
        "gemini:skill",
        "skill-group:test-gemini-ns",
    ])

def _test_gemini_skill_group_output(name):
    gemini_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-gemini-ns",
        install_name = "gemini-install",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _gemini_skill_group_output_impl,
    )

def _gemini_skill_group_output_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("gemini-install.gemini.skill-group.tar"),
    )

# --------------------------------------------------------------------------- #
# claude_subagent_group
# --------------------------------------------------------------------------- #

def _test_claude_subagent_group_tags(name):
    claude_subagent_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _claude_subagent_group_tags_impl,
    )

def _claude_subagent_group_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:claude-agents",
        "claude:agents",
    ])

def _test_claude_subagent_group_output(name):
    claude_subagent_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        install_name = "agents-install",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _claude_subagent_group_output_impl,
    )

def _claude_subagent_group_output_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("agents-install.claude.agents.tar"),
    )

# --------------------------------------------------------------------------- #
# claude_subagent (single file variant)
# --------------------------------------------------------------------------- #

def _test_claude_subagent_tags(name):
    claude_subagent(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _claude_subagent_tags_impl,
    )

def _claude_subagent_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:claude-agents",
        "claude:agents",
    ])

# --------------------------------------------------------------------------- #
# claude_plugin_commands
# --------------------------------------------------------------------------- #

def _test_claude_plugin_commands_tags(name):
    claude_plugin_commands(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _claude_plugin_commands_tags_impl,
    )

def _claude_plugin_commands_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:claude",
        "claude:commands",
    ])

def _test_claude_plugin_commands_output(name):
    claude_plugin_commands(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        install_name = "commands-install",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _claude_plugin_commands_output_impl,
    )

def _claude_plugin_commands_output_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("commands-install.claude.commands.tar"),
    )

# --------------------------------------------------------------------------- #
# cursor_skill_group
# --------------------------------------------------------------------------- #

def _test_cursor_skill_group_tags(name):
    cursor_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-cursor-ns",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _cursor_skill_group_tags_impl,
    )

def _cursor_skill_group_tags_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:cursor",
        "cursor:skill",
        "skill-group:test-cursor-ns",
    ])

def _test_cursor_skill_group_output(name):
    cursor_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "test-cursor-ns",
        install_name = "cursor-install",
        tags = ["manual"],
    )
    analysis_test(
        name = name,
        target = name + "_subject_tar",
        impl = _cursor_skill_group_output_impl,
    )

def _cursor_skill_group_output_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        matching.file_basename_equals("cursor-install.cursor.skill-group.tar"),
    )

# --------------------------------------------------------------------------- #
# extra_tags pass-through
# --------------------------------------------------------------------------- #

def _test_extra_tags_passthrough(name):
    """Extra tags from **kwargs must not be silently dropped."""
    claude_skill_group(
        name = name + "_subject",
        srcs = ["collection.bzl"],
        namespace = "ns",
        tags = ["manual", "extra-tag-1", "extra-tag-2"],
    )
    analysis_test(
        name = name,
        target = name + "_subject",
        impl = _extra_tags_passthrough_impl,
    )

def _extra_tags_passthrough_impl(env, target):
    env.expect.that_target(target).tags().contains_at_least([
        "tool:claude",
        "claude:collection",
        "extra-tag-1",
        "extra-tag-2",
    ])

# --------------------------------------------------------------------------- #
# Suite
# --------------------------------------------------------------------------- #

def collection_test_suite(name):
    test_suite(
        name = name,
        tests = [
            _test_claude_skill_group_tags,
            _test_claude_skill_group_output,
            _test_claude_skill_group_namespace_default,
            _test_cursor_skill_group_tags,
            _test_cursor_skill_group_output,
            _test_gemini_skill_group_tags,
            _test_gemini_skill_group_output,
            _test_claude_subagent_group_tags,
            _test_claude_subagent_group_output,
            _test_claude_subagent_tags,
            _test_claude_plugin_commands_tags,
            _test_claude_plugin_commands_output,
            _test_extra_tags_passthrough,
        ],
    )
