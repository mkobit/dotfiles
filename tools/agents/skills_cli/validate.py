"""SKILL.md validators aligned with the agentskills.io spec.

Each validator is a function with signature:
    (frontmatter: dict, context: ValidationContext) -> list[ValidationResult]

Validators are grouped into registries for composable Bazel test targets.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.agents.skills_cli.frontmatter import FrontmatterError, parse_frontmatter
from tools.agents.skills_cli.validate_models import (
    SkillValidationReport,
    ValidationContext,
    ValidationResult,
)

# Type alias for validator functions
Validator = Callable[[dict[str, Any], ValidationContext], list[ValidationResult]]

# Kebab-case pattern from the agentskills.io spec
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Allowed top-level frontmatter keys per spec
_ALLOWED_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)


# ---------------------------------------------------------------------------
# Spec validators (agentskills.io compliance)
# ---------------------------------------------------------------------------


def validate_name_required(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """name field must be present and non-empty."""
    name = frontmatter.get("name")
    passed = isinstance(name, str) and len(name.strip()) > 0
    return [
        ValidationResult(
            rule_id="spec.name.required",
            severity="error",
            passed=passed,
            message="name is required and must be non-empty" if not passed else "OK",
            field="name",
        )
    ]


def validate_description_required(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """description field must be present and non-empty."""
    desc = frontmatter.get("description")
    passed = isinstance(desc, str) and len(desc.strip()) > 0
    return [
        ValidationResult(
            rule_id="spec.description.required",
            severity="error",
            passed=passed,
            message="description is required and must be non-empty"
            if not passed
            else "OK",
            field="description",
        )
    ]


def validate_name_format(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """name must be kebab-case."""
    name = frontmatter.get("name", "")
    if not isinstance(name, str) or not name:
        # Caught by validate_name_required
        return []
    passed = bool(_KEBAB_RE.match(name))
    return [
        ValidationResult(
            rule_id="spec.name.format",
            severity="error",
            passed=passed,
            message=f"name '{name}' must be kebab-case (^[a-z0-9]+(-[a-z0-9]+)*$)"
            if not passed
            else "OK",
            field="name",
        )
    ]


def validate_name_length(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """name must be at most 64 characters."""
    name = frontmatter.get("name", "")
    if not isinstance(name, str) or not name:
        return []
    passed = len(name) <= 64
    return [
        ValidationResult(
            rule_id="spec.name.length",
            severity="error",
            passed=passed,
            message=f"name is {len(name)} chars, max 64" if not passed else "OK",
            field="name",
        )
    ]


def validate_name_matches_directory(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """name field must match the parent directory name."""
    name = frontmatter.get("name", "")
    if not isinstance(name, str) or not name:
        return []
    passed = name == context.skill_dir_name
    return [
        ValidationResult(
            rule_id="spec.name.matches_directory",
            severity="error",
            passed=passed,
            message=f"name '{name}' does not match directory '{context.skill_dir_name}'"
            if not passed
            else "OK",
            field="name",
        )
    ]


def validate_description_length(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """description must be at most 1024 characters."""
    desc = frontmatter.get("description", "")
    if not isinstance(desc, str) or not desc:
        return []
    passed = len(desc) <= 1024
    return [
        ValidationResult(
            rule_id="spec.description.length",
            severity="error",
            passed=passed,
            message=f"description is {len(desc)} chars, max 1024"
            if not passed
            else "OK",
            field="description",
        )
    ]


def validate_compatibility_length(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """compatibility must be at most 500 characters (if present)."""
    compat = frontmatter.get("compatibility")
    if compat is None:
        return []
    if not isinstance(compat, str):
        return [
            ValidationResult(
                rule_id="spec.compatibility.length",
                severity="error",
                passed=False,
                message="compatibility must be a string",
                field="compatibility",
            )
        ]
    passed = len(compat) <= 500
    return [
        ValidationResult(
            rule_id="spec.compatibility.length",
            severity="error",
            passed=passed,
            message=f"compatibility is {len(compat)} chars, max 500"
            if not passed
            else "OK",
            field="compatibility",
        )
    ]


def validate_metadata_value_types(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """metadata must be a string-to-string mapping (if present)."""
    meta = frontmatter.get("metadata")
    if meta is None:
        return []
    if not isinstance(meta, dict):
        return [
            ValidationResult(
                rule_id="spec.metadata.value_types",
                severity="error",
                passed=False,
                message="metadata must be a mapping",
                field="metadata",
            )
        ]
    bad_keys = [k for k, v in meta.items() if not isinstance(v, str)]
    passed = len(bad_keys) == 0
    return [
        ValidationResult(
            rule_id="spec.metadata.value_types",
            severity="error",
            passed=passed,
            message=f"metadata values must be strings, bad keys: {bad_keys}"
            if not passed
            else "OK",
            field="metadata",
        )
    ]


def validate_allowed_keys(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """Only allowed top-level keys per spec."""
    extra = set(frontmatter.keys()) - _ALLOWED_KEYS
    passed = len(extra) == 0
    return [
        ValidationResult(
            rule_id="spec.keys.allowed",
            severity="error",
            passed=passed,
            message=f"unexpected keys: {sorted(extra)}" if not passed else "OK",
        )
    ]


# ---------------------------------------------------------------------------
# Lint validators (project-specific)
# ---------------------------------------------------------------------------


def validate_description_usage_hint(
    frontmatter: dict[str, Any], context: ValidationContext
) -> list[ValidationResult]:
    """Description should mention when to use the skill."""
    desc = frontmatter.get("description", "")
    if not isinstance(desc, str) or not desc:
        return []
    keywords = ["when", "use this", "use when", "activates", "for"]
    passed = any(kw in desc.lower() for kw in keywords)
    return [
        ValidationResult(
            rule_id="lint.description.usage_hint",
            severity="warning",
            passed=passed,
            message="description should mention when to use the skill"
            if not passed
            else "OK",
            field="description",
        )
    ]


# ---------------------------------------------------------------------------
# Structure validators (folder-level, not frontmatter-based)
# ---------------------------------------------------------------------------


def validate_structure(skill_dir: Path) -> list[ValidationResult]:
    """Validate skill directory structure.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of validation results for structure checks.
    """
    results: list[ValidationResult] = []

    # SKILL.md must exist
    skill_md = skill_dir / "SKILL.md"
    results.append(
        ValidationResult(
            rule_id="structure.skill_md.exists",
            severity="error",
            passed=skill_md.is_file(),
            message=f"SKILL.md not found in {skill_dir}"
            if not skill_md.is_file()
            else "OK",
            field="SKILL.md",
        )
    )

    # Known subdirectories must be directories if present
    known_dirs = ["scripts", "references", "assets"]
    for dirname in known_dirs:
        candidate = skill_dir / dirname
        if candidate.exists() and not candidate.is_dir():
            results.append(
                ValidationResult(
                    rule_id="structure.known_dirs",
                    severity="error",
                    passed=False,
                    message=f"'{dirname}' exists but is not a directory",
                    field=dirname,
                )
            )

    return results


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SPEC_VALIDATORS: list[Validator] = [
    validate_name_required,
    validate_description_required,
    validate_name_format,
    validate_name_length,
    validate_name_matches_directory,
    validate_description_length,
    validate_compatibility_length,
    validate_metadata_value_types,
    validate_allowed_keys,
]

LINT_VALIDATORS: list[Validator] = [
    validate_description_usage_hint,
]

ALL_VALIDATORS: list[Validator] = SPEC_VALIDATORS + LINT_VALIDATORS


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def validate_skill(
    skill_dir: Path,
    validators: list[Validator] | None = None,
    include_structure: bool = True,
) -> SkillValidationReport:
    """Validate a single skill directory.

    Args:
        skill_dir: Path to the skill directory.
        validators: Frontmatter validators to run (defaults to ALL_VALIDATORS).
        include_structure: Whether to run structure validators.

    Returns:
        Aggregated validation report.
    """
    if validators is None:
        validators = ALL_VALIDATORS

    skill_name = skill_dir.name
    results: list[ValidationResult] = []

    # Structure validation first
    if include_structure:
        results.extend(validate_structure(skill_dir))

    # Parse frontmatter
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return SkillValidationReport(skill_name=skill_name, results=results)

    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except FrontmatterError as exc:
        results.append(
            ValidationResult(
                rule_id="spec.frontmatter.parse",
                severity="error",
                passed=False,
                message=str(exc),
            )
        )
        return SkillValidationReport(skill_name=skill_name, results=results)

    context = ValidationContext(
        skill_dir_name=skill_name,
        path=skill_dir,
        raw_frontmatter=frontmatter,
    )

    for validator in validators:
        results.extend(validator(frontmatter, context))

    return SkillValidationReport(skill_name=skill_name, results=results)
