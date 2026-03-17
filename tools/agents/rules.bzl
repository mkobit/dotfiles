"""
Macros for portable Agent Skills testing.

Generates drift tests (diff_test) for canonical skills
and their committed copies.
"""

load("@bazel_skylib//rules:diff_test.bzl", "diff_test")

def skills_drift_tests(name, skills, tools, chezmoi_package):
    """Generates diff_test targets for each skill x tool combination.

    Call from the canonical skills package so that skill files are local.

    Args:
        name: Base name for the test suite.
        skills: List of skill directory names (use a glob-derived list).
        tools: List of target tool names (e.g., ["claude", "gemini", "cursor"]).
        chezmoi_package: Label path to the chezmoi source package (e.g., "//src/chezmoi").
    """
    tests = []
    for skill in skills:
        for tool in tools:
            test_name = "{name}_{tool}_{skill}".format(
                name = name,
                tool = tool,
                skill = skill,
            )
            diff_test(
                name = test_name,
                file1 = "{skill}/SKILL.md".format(skill = skill),
                file2 = "{pkg}:dot_{tool}/skills/{skill}/SKILL.md".format(
                    pkg = chezmoi_package,
                    tool = tool,
                    skill = skill,
                ),
            )
            tests.append(":" + test_name)

    native.test_suite(
        name = name,
        tests = tests,
    )
