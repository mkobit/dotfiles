"""Unit tests for SKILL.md validation framework."""

from pathlib import Path
from typing import Any

import pytest

from tools.agents.skills_cli.frontmatter import FrontmatterError, parse_frontmatter
from tools.agents.skills_cli.validate import (
    ALL_VALIDATORS,
    LINT_VALIDATORS,
    SPEC_VALIDATORS,
    validate_allowed_keys,
    validate_compatibility_length,
    validate_description_length,
    validate_description_required,
    validate_description_usage_hint,
    validate_metadata_value_types,
    validate_name_format,
    validate_name_length,
    validate_name_matches_directory,
    validate_name_required,
    validate_skill,
    validate_structure,
)
from tools.agents.skills_cli.validate_models import ValidationContext


def _ctx(
    name: str = "my-skill", frontmatter: dict[str, Any] | None = None
) -> ValidationContext:
    """Create a minimal ValidationContext for testing."""
    return ValidationContext(
        skill_dir_name=name,
        path=Path(f"/fake/{name}"),
        raw_frontmatter=frontmatter or {},
    )


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        text = "---\nname: my-skill\ndescription: A skill\n---\n# Body"
        result = parse_frontmatter(text)
        assert result == {"name": "my-skill", "description": "A skill"}

    def test_missing_opening_delimiter(self) -> None:
        with pytest.raises(FrontmatterError, match="Missing opening"):
            parse_frontmatter("name: my-skill\n---\n")

    def test_missing_closing_delimiter(self) -> None:
        with pytest.raises(FrontmatterError, match="Missing closing"):
            parse_frontmatter("---\nname: my-skill\n")

    def test_empty_frontmatter(self) -> None:
        with pytest.raises(FrontmatterError, match="Empty frontmatter"):
            parse_frontmatter("---\n\n---\n")

    def test_invalid_yaml(self) -> None:
        with pytest.raises(FrontmatterError, match="Invalid YAML"):
            parse_frontmatter("---\n: : :\n---\n")

    def test_non_dict_frontmatter(self) -> None:
        with pytest.raises(FrontmatterError, match="must be a YAML mapping"):
            parse_frontmatter("---\n- item1\n- item2\n---\n")

    def test_leading_whitespace(self) -> None:
        text = "\n  ---\nname: my-skill\n---\n"
        result = parse_frontmatter(text)
        assert result["name"] == "my-skill"

    def test_metadata_field(self) -> None:
        text = '---\nname: my-skill\nmetadata:\n  key: "value"\n---\n'
        result = parse_frontmatter(text)
        assert result["metadata"] == {"key": "value"}


# ---------------------------------------------------------------------------
# Spec validators
# ---------------------------------------------------------------------------


class TestNameRequired:
    def test_pass(self) -> None:
        results = validate_name_required({"name": "my-skill"}, _ctx())
        assert len(results) == 1
        assert results[0].passed

    def test_fail_missing(self) -> None:
        results = validate_name_required({}, _ctx())
        assert not results[0].passed

    def test_fail_empty(self) -> None:
        results = validate_name_required({"name": ""}, _ctx())
        assert not results[0].passed

    def test_fail_whitespace(self) -> None:
        results = validate_name_required({"name": "  "}, _ctx())
        assert not results[0].passed


class TestDescriptionRequired:
    def test_pass(self) -> None:
        results = validate_description_required({"description": "A skill"}, _ctx())
        assert results[0].passed

    def test_fail_missing(self) -> None:
        results = validate_description_required({}, _ctx())
        assert not results[0].passed

    def test_fail_empty(self) -> None:
        results = validate_description_required({"description": ""}, _ctx())
        assert not results[0].passed


class TestNameFormat:
    def test_pass_simple(self) -> None:
        results = validate_name_format({"name": "my-skill"}, _ctx())
        assert results[0].passed

    def test_pass_single_word(self) -> None:
        results = validate_name_format({"name": "skill"}, _ctx())
        assert results[0].passed

    def test_pass_with_numbers(self) -> None:
        results = validate_name_format({"name": "skill-v2"}, _ctx())
        assert results[0].passed

    def test_fail_uppercase(self) -> None:
        results = validate_name_format({"name": "My-Skill"}, _ctx())
        assert not results[0].passed

    def test_fail_spaces(self) -> None:
        results = validate_name_format({"name": "my skill"}, _ctx())
        assert not results[0].passed

    def test_fail_underscores(self) -> None:
        results = validate_name_format({"name": "my_skill"}, _ctx())
        assert not results[0].passed

    def test_skip_when_empty(self) -> None:
        results = validate_name_format({"name": ""}, _ctx())
        assert len(results) == 0


class TestNameLength:
    def test_pass(self) -> None:
        results = validate_name_length({"name": "a" * 64}, _ctx())
        assert results[0].passed

    def test_fail(self) -> None:
        results = validate_name_length({"name": "a" * 65}, _ctx())
        assert not results[0].passed

    def test_skip_when_empty(self) -> None:
        results = validate_name_length({"name": ""}, _ctx())
        assert len(results) == 0


class TestNameMatchesDirectory:
    def test_pass(self) -> None:
        results = validate_name_matches_directory(
            {"name": "my-skill"}, _ctx("my-skill")
        )
        assert results[0].passed

    def test_fail(self) -> None:
        results = validate_name_matches_directory(
            {"name": "other-name"}, _ctx("my-skill")
        )
        assert not results[0].passed

    def test_skip_when_empty(self) -> None:
        results = validate_name_matches_directory({"name": ""}, _ctx())
        assert len(results) == 0


class TestDescriptionLength:
    def test_pass(self) -> None:
        results = validate_description_length({"description": "x" * 1024}, _ctx())
        assert results[0].passed

    def test_fail(self) -> None:
        results = validate_description_length({"description": "x" * 1025}, _ctx())
        assert not results[0].passed

    def test_skip_when_empty(self) -> None:
        results = validate_description_length({"description": ""}, _ctx())
        assert len(results) == 0


class TestCompatibilityLength:
    def test_pass(self) -> None:
        results = validate_compatibility_length({"compatibility": "x" * 500}, _ctx())
        assert results[0].passed

    def test_fail(self) -> None:
        results = validate_compatibility_length({"compatibility": "x" * 501}, _ctx())
        assert not results[0].passed

    def test_skip_when_absent(self) -> None:
        results = validate_compatibility_length({}, _ctx())
        assert len(results) == 0

    def test_fail_non_string(self) -> None:
        results = validate_compatibility_length({"compatibility": 42}, _ctx())
        assert not results[0].passed


class TestMetadataValueTypes:
    def test_pass(self) -> None:
        results = validate_metadata_value_types({"metadata": {"key": "value"}}, _ctx())
        assert results[0].passed

    def test_fail_non_string_value(self) -> None:
        results = validate_metadata_value_types({"metadata": {"key": 42}}, _ctx())
        assert not results[0].passed

    def test_fail_non_dict(self) -> None:
        results = validate_metadata_value_types({"metadata": "string"}, _ctx())
        assert not results[0].passed

    def test_skip_when_absent(self) -> None:
        results = validate_metadata_value_types({}, _ctx())
        assert len(results) == 0


class TestAllowedKeys:
    def test_pass(self) -> None:
        fm = {"name": "x", "description": "y", "license": "MIT"}
        results = validate_allowed_keys(fm, _ctx())
        assert results[0].passed

    def test_fail_extra_key(self) -> None:
        fm = {"name": "x", "description": "y", "author": "me"}
        results = validate_allowed_keys(fm, _ctx())
        assert not results[0].passed
        assert "author" in results[0].message


# ---------------------------------------------------------------------------
# Lint validators
# ---------------------------------------------------------------------------


class TestDescriptionUsageHint:
    def test_pass_with_when(self) -> None:
        results = validate_description_usage_hint(
            {"description": "Use when writing docs"}, _ctx()
        )
        assert results[0].passed

    def test_pass_with_use_this(self) -> None:
        results = validate_description_usage_hint(
            {"description": "Use this for code review"}, _ctx()
        )
        assert results[0].passed

    def test_fail_no_hint(self) -> None:
        results = validate_description_usage_hint(
            {"description": "A great skill"}, _ctx()
        )
        assert not results[0].passed
        assert results[0].severity == "warning"


# ---------------------------------------------------------------------------
# Structure validators
# ---------------------------------------------------------------------------


class TestValidateStructure:
    def test_pass(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        results = validate_structure(skill_dir)
        assert all(r.passed for r in results)

    def test_fail_missing_skill_md(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        results = validate_structure(skill_dir)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 1
        assert failed[0].rule_id == "structure.skill_md.exists"

    def test_fail_known_dir_is_file(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        (skill_dir / "scripts").write_text("not a directory")
        results = validate_structure(skill_dir)
        failed = [r for r in results if not r.passed]
        assert len(failed) == 1
        assert failed[0].rule_id == "structure.known_dirs"

    def test_pass_with_known_subdirs(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "references").mkdir()
        results = validate_structure(skill_dir)
        assert all(r.passed for r in results)


# ---------------------------------------------------------------------------
# Composite runner
# ---------------------------------------------------------------------------


class TestValidateSkill:
    def test_valid_skill(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Use when you need help\n---\n# Body"
        )
        report = validate_skill(skill_dir)
        assert report.passed
        assert report.error_count == 0

    def test_invalid_name_format(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: My Skill\ndescription: Use when you need help\n---\n"
        )
        report = validate_skill(skill_dir, validators=SPEC_VALIDATORS)
        assert not report.passed
        assert report.error_count > 0

    def test_missing_frontmatter(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Just a heading\n")
        report = validate_skill(skill_dir)
        assert not report.passed

    def test_lint_only(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: A great skill\n---\n"
        )
        report = validate_skill(
            skill_dir, validators=LINT_VALIDATORS, include_structure=False
        )
        # Lint warning should fire (no usage hint)
        assert report.warning_count == 1
        # But no error-severity failures
        assert report.passed

    def test_registries_not_empty(self) -> None:
        assert len(SPEC_VALIDATORS) > 0
        assert len(LINT_VALIDATORS) > 0
        assert len(ALL_VALIDATORS) == len(SPEC_VALIDATORS) + len(LINT_VALIDATORS)
