"""Standalone test runner for Bazel py_test targets.

Parses --mode, --skill-md, --skill-dir-name from command-line args.
Calls appropriate validators and exits non-zero on error-severity failures.

No Click dependency — invoked by Bazel with positional args.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.agents.skills_cli.frontmatter import FrontmatterError, parse_frontmatter
from tools.agents.skills_cli.validate import (
    LINT_VALIDATORS,
    SPEC_VALIDATORS,
    Validator,
    validate_structure,
)
from tools.agents.skills_cli.validate_models import ValidationContext, ValidationResult


def _run_frontmatter_validators(
    skill_md: Path,
    skill_dir_name: str,
    validators: list[Validator],
) -> list[ValidationResult]:
    """Parse frontmatter and run the given validators."""
    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except FrontmatterError as exc:
        return [
            ValidationResult(
                rule_id="spec.frontmatter.parse",
                severity="error",
                passed=False,
                message=str(exc),
            )
        ]

    context = ValidationContext(
        skill_dir_name=skill_dir_name,
        path=skill_md.parent,
        raw_frontmatter=frontmatter,
    )

    results: list[ValidationResult] = []
    for validator in validators:
        results.extend(validator(frontmatter, context))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="SKILL.md validation test runner")
    parser.add_argument(
        "--mode",
        choices=["spec", "lint", "structure"],
        required=True,
        help="Validation mode",
    )
    parser.add_argument(
        "--skill-md",
        type=Path,
        required=True,
        help="Path to SKILL.md file",
    )
    parser.add_argument(
        "--skill-dir-name",
        type=str,
        required=True,
        help="Expected skill directory name",
    )

    args = parser.parse_args()

    if not args.skill_md.is_file():
        print(f"FAIL: SKILL.md not found: {args.skill_md}")
        sys.exit(1)

    results: list[ValidationResult] = []

    if args.mode == "spec":
        results = _run_frontmatter_validators(
            args.skill_md, args.skill_dir_name, SPEC_VALIDATORS
        )
    elif args.mode == "lint":
        results = _run_frontmatter_validators(
            args.skill_md, args.skill_dir_name, LINT_VALIDATORS
        )
    elif args.mode == "structure":
        results = validate_structure(args.skill_md.parent)

    errors = [r for r in results if r.severity == "error" and not r.passed]
    warnings = [r for r in results if r.severity == "warning" and not r.passed]

    if warnings:
        for w in warnings:
            print(f"WARN [{w.rule_id}]: {w.message}")

    if errors:
        for e in errors:
            print(f"FAIL [{e.rule_id}]: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
