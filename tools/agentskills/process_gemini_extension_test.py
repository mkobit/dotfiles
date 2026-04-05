"""Tests for process_gemini_extension.py — validates SkillIR emission for Gemini extensions."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from tools.agentskills.process_gemini_extension import main


def test_clean_name_collapses_hyphens(tmp_path: Path) -> None:
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    ext_json = ext_dir / "extension.json"

    # "My  Extension" has double spaces and mixed case
    # Under previous logic it became "my--extension"
    # Now it should be "my-extension"
    ext_data = {"name": "My  Extension", "version": "1.2.3"}
    ext_json.write_text(json.dumps(ext_data), encoding="utf-8")

    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(ext_json), str(output)])

    assert result.exit_code == 0, result.output
    assert output.exists()

    data = json.loads(output.read_text())
    assert data["name"] == "my-extension"
    assert data["description"] == "Gemini Extension: My  Extension v1.2.3"
    assert data["source_format"] == "gemini-extension"
