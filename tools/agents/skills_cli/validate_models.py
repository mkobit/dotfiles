"""Data models for SKILL.md validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel


class ValidationContext(BaseModel):
    """Context about the skill being validated."""

    skill_dir_name: str
    path: Path
    raw_frontmatter: dict[str, Any]


class ValidationResult(BaseModel):
    """Result of a single validation rule."""

    rule_id: str
    severity: Literal["error", "warning", "info"]
    passed: bool
    message: str
    field: str | None = None


class SkillValidationReport(BaseModel):
    """Aggregated validation results for a single skill."""

    skill_name: str
    results: list[ValidationResult]

    @property
    def passed(self) -> bool:
        """True if no error-severity rules failed."""
        return all(r.passed for r in self.results if r.severity == "error")

    @property
    def error_count(self) -> int:
        """Number of error-severity failures."""
        return sum(1 for r in self.results if r.severity == "error" and not r.passed)

    @property
    def warning_count(self) -> int:
        """Number of warning-severity failures."""
        return sum(1 for r in self.results if r.severity == "warning" and not r.passed)
