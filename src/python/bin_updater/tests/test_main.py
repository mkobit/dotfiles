import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bin_updater.main import app
from bin_updater.service import ToolUpdateResult

runner = CliRunner()


def test_main_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Automate chezmoi binary tools upgrades" in result.stdout


def test_main_no_arguments() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "specify either --tool <name> or --all" in result.stderr or "specify either --tool" in result.stdout


def test_main_missing_tool(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--tool", "nonexistent", "--catalog-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "Catalog file not found" in result.stderr or "Catalog file not found" in result.stdout


def test_main_with_updates(tmp_path: Path, monkeypatch) -> None:
    catalog_file = tmp_path / "app.toml"
    catalog_file.write_text(
        '[bin.app]\nversion = "1.0.0"\n[bin.app.github_releases]\nrepo = "org/app"\n'
        'tag_format = "v{version}"\nfilename_format = "app-{target}"\n[bin.app.github_releases.platforms]\nlinux_amd64 = "x"\n',
        encoding="utf-8",
    )

    fake_results = [
        ToolUpdateResult(tool_name="app", changed=True, old_version="1.0.0", new_version="2.0.0"),
    ]
    monkeypatch.setattr("bin_updater.main.run_updates", lambda _cats, _client, dry_run=False: fake_results)

    result = runner.invoke(app, ["--all", "--catalog-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Upgraded app: 1.0.0 -> 2.0.0" in result.stdout


def test_main_skips_non_github_release_tool(tmp_path: Path) -> None:
    catalog_file = tmp_path / "chafa.toml"
    catalog_file.write_text('[bin.chafa]\nversion = "1.14.0"\n', encoding="utf-8")
    result = runner.invoke(app, ["--tool", "chafa", "--catalog-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Skipping chafa" in result.stdout


def test_main_writes_result_report(tmp_path: Path, monkeypatch) -> None:
    report = tmp_path / "report.json"
    report.write_text("stale")
    expected = ToolUpdateResult(tool_name="app", changed=True, old_version="1", new_version="2")
    monkeypatch.setattr("bin_updater.main.run_updates", lambda *_args, **_kwargs: [expected])
    result = runner.invoke(app, ["--all", "--catalog-dir", str(tmp_path), "--report-file", str(report)])
    assert result.exit_code == 0
    assert json.loads(report.read_text()) == [expected.model_dump()]
    assert "pr_title" in json.loads(report.read_text())[0]
    assert "pr_body" in json.loads(report.read_text())[0]


@pytest.mark.parametrize("case", ["no_argument", "missing", "vendor", "invalid"])
def test_main_clears_stale_reports(tmp_path: Path, case: str) -> None:
    report = tmp_path / "report.json"
    report.write_text('[{"changed": true}]')
    args = ["--report-file", str(report), "--catalog-dir", str(tmp_path)]
    if case != "no_argument":
        args.extend(["--tool", "app"])
    if case == "vendor":
        (tmp_path / "app.toml").write_text('[bin.app]\nversion = "1"')
    if case == "invalid":
        (tmp_path / "app.toml").write_text("invalid toml ]")
    result = runner.invoke(app, args)
    assert result.exit_code == (0 if case == "vendor" else 1)
    assert json.loads(report.read_text()) == []
