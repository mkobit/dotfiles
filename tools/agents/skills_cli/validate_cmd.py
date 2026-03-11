"""Entry point for skill validation: bazel run //tools/agents:validate."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from tools.agents.skills_cli.core import discover_local_skills
from tools.agents.skills_cli.validate import (
    ALL_VALIDATORS,
    LINT_VALIDATORS,
    SPEC_VALIDATORS,
    validate_skill,
)
from tools.agents.skills_cli.validate_models import SkillValidationReport


@click.command()
@click.option(
    "--workspace",
    envvar="BUILD_WORKSPACE_DIRECTORY",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Workspace root (set automatically by bazel run).",
)
@click.option("--spec-only", is_flag=True, help="Run only spec validators.")
@click.option("--lint-only", is_flag=True, help="Run only lint validators.")
@click.option("--verbose/--quiet", default=True, help="Print detailed results.")
def main(workspace: Path, spec_only: bool, lint_only: bool, verbose: bool) -> None:
    """Validate all canonical SKILL.md files."""
    canonical_dir = workspace / "src" / "agents" / "skills"
    skills = discover_local_skills(canonical_dir)

    if not skills:
        click.echo("No skills found.")
        sys.exit(1)

    validators = ALL_VALIDATORS
    if spec_only:
        validators = SPEC_VALIDATORS
    elif lint_only:
        validators = LINT_VALIDATORS

    include_structure = not spec_only and not lint_only

    reports: list[SkillValidationReport] = []
    for skill in skills:
        report = validate_skill(
            skill.path,
            validators=validators,
            include_structure=include_structure,
        )
        reports.append(report)

        if verbose:
            status = "PASS" if report.passed else "FAIL"
            click.echo(f"  {status}  {skill.name}")
            for r in report.results:
                if not r.passed:
                    icon = "E" if r.severity == "error" else "W"
                    click.echo(f"    [{icon}] {r.rule_id}: {r.message}")

    total_errors = sum(r.error_count for r in reports)
    total_warnings = sum(r.warning_count for r in reports)

    click.echo()
    click.echo(
        f"Validated {len(reports)} skill(s): "
        f"{total_errors} error(s), {total_warnings} warning(s)"
    )

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
