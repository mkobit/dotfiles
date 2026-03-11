"""YAML frontmatter parser for SKILL.md files.

Extracts text between ``---`` delimiters and parses with ``yaml.safe_load``.
Aligns with upstream ``quick_validate.py`` patterns.
"""

from __future__ import annotations

from typing import Any

import yaml  # type: ignore[import-untyped]


class FrontmatterError(Exception):
    """Raised when frontmatter is missing or malformed."""


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file.

    Args:
        text: Full file contents.

    Returns:
        Parsed frontmatter as a dict.

    Raises:
        FrontmatterError: If frontmatter delimiters are missing or YAML is invalid.
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        raise FrontmatterError("Missing opening frontmatter delimiter (---)")

    # Find the closing delimiter after the opening one
    rest = stripped[3:]
    end_idx = rest.find("\n---")
    if end_idx == -1:
        raise FrontmatterError("Missing closing frontmatter delimiter (---)")

    yaml_text = rest[:end_idx]
    if not yaml_text.strip():
        raise FrontmatterError("Empty frontmatter block")

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"Invalid YAML in frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise FrontmatterError(
            f"Frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    return data
