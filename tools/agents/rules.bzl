"""
Macros for portable Agent Skills testing.

Generates drift tests (diff_test) and validation tests (py_test)
for canonical skills and their committed copies.
"""

load("@bazel_skylib//rules:diff_test.bzl", "diff_test")
load("@rules_python//python:defs.bzl", "py_test")

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

def upstream_skill_drift_tests(name, skills, tools, chezmoi_package, external_repo):
    """Generates py_test targets for upstream skills (directory-level comparison).

    Compares the full skill directory from an http_archive external repo
    against the committed copy in each tool's chezmoi source directory.

    Args:
        name: Base name for the test suite.
        skills: List of upstream skill directory names (e.g., ["skill-creator"]).
        tools: List of target tool names (e.g., ["claude", "gemini", "cursor"]).
        chezmoi_package: Label path to the chezmoi source package.
        external_repo: Name of the http_archive repo containing upstream skills.
    """
    tests = []
    for skill in skills:
        skill_under = skill.replace("-", "_")
        for tool in tools:
            test_name = "{name}_{tool}_{skill}".format(
                name = name,
                tool = tool,
                skill = skill_under,
            )
            py_test(
                name = test_name,
                srcs = ["//tools/agents/skills_cli:dir_diff.py"],
                main = "dir_diff.py",
                args = [
                    "$(rootpath @{repo}//:skills/{skill}/SKILL.md)".format(
                        repo = external_repo,
                        skill = skill,
                    ),
                    "$(rootpath {pkg}:dot_{tool}/skills/{skill}/SKILL.md)".format(
                        pkg = chezmoi_package,
                        tool = tool,
                        skill = skill,
                    ),
                ],
                data = [
                    # Filegroups for full directory comparison
                    "@{repo}//:{skill_under}_files".format(
                        repo = external_repo,
                        skill_under = skill_under,
                    ),
                    "{pkg}:dot_{tool}_{skill_under}_files".format(
                        pkg = chezmoi_package,
                        tool = tool,
                        skill_under = skill_under,
                    ),
                    # Individual SKILL.md markers for $(rootpath) resolution
                    "@{repo}//:skills/{skill}/SKILL.md".format(
                        repo = external_repo,
                        skill = skill,
                    ),
                    "{pkg}:dot_{tool}/skills/{skill}/SKILL.md".format(
                        pkg = chezmoi_package,
                        tool = tool,
                        skill = skill,
                    ),
                ],
                deps = ["//tools/agents/skills_cli:skills_cli_lib"],
            )
            tests.append(":" + test_name)

    native.test_suite(
        name = name,
        tests = tests,
    )

def skill_frontmatter_test(name, skill_md, skill_dir_name):
    """Generates a py_test that validates SKILL.md spec compliance.

    Args:
        name: Test target name.
        skill_md: Label for the SKILL.md file.
        skill_dir_name: Expected skill directory name (kebab-case).
    """
    py_test(
        name = name,
        srcs = ["//tools/agents/skills_cli:validate_test_runner.py"],
        main = "validate_test_runner.py",
        args = [
            "--mode",
            "spec",
            "--skill-md",
            "$(rootpath {})".format(skill_md),
            "--skill-dir-name",
            skill_dir_name,
        ],
        data = [skill_md],
        deps = ["//tools/agents/skills_cli:skills_cli_lib"],
    )

def skill_lint_test(name, skill_md, skill_dir_name):
    """Generates a py_test that validates SKILL.md lint rules.

    Args:
        name: Test target name.
        skill_md: Label for the SKILL.md file.
        skill_dir_name: Expected skill directory name (kebab-case).
    """
    py_test(
        name = name,
        srcs = ["//tools/agents/skills_cli:validate_test_runner.py"],
        main = "validate_test_runner.py",
        args = [
            "--mode",
            "lint",
            "--skill-md",
            "$(rootpath {})".format(skill_md),
            "--skill-dir-name",
            skill_dir_name,
        ],
        data = [skill_md],
        deps = ["//tools/agents/skills_cli:skills_cli_lib"],
    )

def skill_structure_test(name, skill_md, skill_dir_name):
    """Generates a py_test that validates skill directory structure.

    Args:
        name: Test target name.
        skill_md: Label for the SKILL.md file (used to locate the skill dir).
        skill_dir_name: Expected skill directory name.
    """
    py_test(
        name = name,
        srcs = ["//tools/agents/skills_cli:validate_test_runner.py"],
        main = "validate_test_runner.py",
        args = [
            "--mode",
            "structure",
            "--skill-md",
            "$(rootpath {})".format(skill_md),
            "--skill-dir-name",
            skill_dir_name,
        ],
        data = [skill_md],
        deps = ["//tools/agents/skills_cli:skills_cli_lib"],
    )

def skill_validation_tests(name, skills):
    """Generates spec, lint, and structure tests for each skill.

    Creates 3 py_test targets per skill, grouped into a test_suite.

    Args:
        name: Base name for the test suite.
        skills: List of skill directory names.
    """
    tests = []
    for skill in skills:
        skill_under = skill.replace("-", "_")
        skill_md = "{}/SKILL.md".format(skill)

        spec_name = "{name}_spec_{skill}".format(name = name, skill = skill_under)
        skill_frontmatter_test(
            name = spec_name,
            skill_md = skill_md,
            skill_dir_name = skill,
        )
        tests.append(":" + spec_name)

        lint_name = "{name}_lint_{skill}".format(name = name, skill = skill_under)
        skill_lint_test(
            name = lint_name,
            skill_md = skill_md,
            skill_dir_name = skill,
        )
        tests.append(":" + lint_name)

        structure_name = "{name}_structure_{skill}".format(name = name, skill = skill_under)
        skill_structure_test(
            name = structure_name,
            skill_md = skill_md,
            skill_dir_name = skill,
        )
        tests.append(":" + structure_name)

    native.test_suite(
        name = name,
        tests = tests,
    )
