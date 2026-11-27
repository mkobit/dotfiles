import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bin_updater.main import app
from bin_updater.policy import load_policy
from bin_updater.service import ToolUpdateResult

runner = CliRunner()


@pytest.fixture(autouse=True)
def stub_chezmoi_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("bin_updater.main.load_policy", lambda _source: {"minimum_release_age": "7d"})


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
    notes = "🚀" * 150_000 + "Final release note."
    expected = ToolUpdateResult(tool_name="app", changed=True, old_version="1", new_version="2", pr_body=notes)
    monkeypatch.setattr("bin_updater.main.run_updates", lambda *_args, **_kwargs: [expected])
    result = runner.invoke(app, ["--all", "--catalog-dir", str(tmp_path), "--report-file", str(report)])
    assert result.exit_code == 0
    assert report.stat().st_size > 512_000
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


@pytest.mark.parametrize("stdout", ['{"bin_updates": {"minimum_release_age": "5d"}}', "not JSON", None])
def test_load_policy_uses_chezmoi_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stdout: str | None) -> None:
    def run(
        args: tuple[str, ...], *, check: bool, capture_output: bool, text: bool, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        assert args[:3] == ("chezmoi", "--source", str(tmp_path))
        assert args[-2:] == ("data", "--format=json")
        assert check and capture_output and text
        if stdout is None:
            raise subprocess.CalledProcessError(1, args, stderr="init not called")
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr("chezmoi_cli.cli.subprocess.run", run)
    if stdout is None or stdout == "not JSON":
        with pytest.raises(ValueError, match="Could not read binary update policy"):
            load_policy(tmp_path)
    else:
        assert load_policy(tmp_path) == {"minimum_release_age": "5d"}


def test_main_handoff_dir_writes_changed_and_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    catalog_dir = tmp_path / "catalogs"
    catalog_dir.mkdir()
    for name in ("changed_app", "unchanged_app", "failed_app"):
        (catalog_dir / f"{name}.toml").write_text(
            f'[bin.{name}]\nversion = "2.0.0"\n[bin.{name}.github_releases]\nrepo = "org/{name}"\n'
            f'tag_format = "v{{version}}"\nfilename_format = "{name}-{{target}}"\n'
            f'[bin.{name}.github_releases.platforms]\nlinux_amd64 = "x"\n',
            encoding="utf-8",
        )
    handoff_dir = tmp_path / "handoff"
    fake_results = [
        ToolUpdateResult(
            tool_name="changed_app",
            changed=True,
            old_version="1.0.0",
            new_version="2.0.0",
            pr_title="chore(deps): bump changed_app from 1.0.0 to 2.0.0",
            pr_body="Notes",
        ),
        ToolUpdateResult(tool_name="unchanged_app", changed=False, old_version="2.0.0", new_version="2.0.0"),
        ToolUpdateResult(
            tool_name="failed_app",
            changed=False,
            old_version="2.0.0",
            new_version="2.0.0",
            error="rate limited",
        ),
    ]
    monkeypatch.setattr("bin_updater.main.run_updates", lambda _cats, _client, dry_run=False: fake_results)

    result = runner.invoke(app, ["--all", "--catalog-dir", str(catalog_dir), "--handoff-dir", str(handoff_dir)])
    assert result.exit_code == 1
    assert (handoff_dir / "changed_app.toml").read_text(encoding="utf-8") == (
        catalog_dir / "changed_app.toml"
    ).read_text(encoding="utf-8")
    assert json.loads((handoff_dir / "changed_app.json").read_text(encoding="utf-8")) == [fake_results[0].model_dump()]
    assert not (handoff_dir / "unchanged_app.toml").exists()
    assert not (handoff_dir / "unchanged_app.json").exists()
    assert not (handoff_dir / "failed_app.toml").exists()
    assert (handoff_dir / "failures.txt").read_text(encoding="utf-8") == "failed_app\n"
