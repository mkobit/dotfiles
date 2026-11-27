import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from chezmoi_cli import (
    Apply,
    Cat,
    ChezmoiCli,
    ExecuteTemplate,
    build_argv,
    format_command,
)


def test_global_options_order_and_serialization(tmp_path: Path) -> None:
    cli = ChezmoiCli(
        executable="/usr/local/bin/chezmoi",
        source=tmp_path / "source",
        cache=tmp_path / "cache",
        config=tmp_path / "config.toml",
        config_format="toml",
        destination=tmp_path / "dest",
        persistent_state=tmp_path / "state.boltdb",
        no_tty=True,
        force=True,
        refresh_externals="always",
    )

    assert cli.data(format="json").argv == (
        "/usr/local/bin/chezmoi",
        "--source",
        str(tmp_path / "source"),
        "--cache",
        str(tmp_path / "cache"),
        "--config",
        str(tmp_path / "config.toml"),
        "--config-format",
        "toml",
        "--destination",
        str(tmp_path / "dest"),
        "--persistent-state",
        str(tmp_path / "state.boltdb"),
        "--no-tty",
        "--force",
        "--refresh-externals=always",
        "data",
        "--format=json",
    )


def test_with_options_returns_new_instance() -> None:
    base = ChezmoiCli(source=Path("/src"), config="/dev/null", config_format="toml")
    updated = base.with_options(destination=Path("/dest"), no_tty=True)

    assert base.destination is None
    assert base.no_tty is False
    assert updated.source == Path("/src")
    assert updated.config == "/dev/null"
    assert updated.config_format == "toml"
    assert updated.destination == Path("/dest")
    assert updated.no_tty is True


def test_subcommands_build_expected_argv(tmp_path: Path) -> None:
    cli = ChezmoiCli(source=tmp_path)

    assert cli.apply("~/.bashrc", force=True, exclude=("scripts", "externals"), refresh_externals="never").argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "apply",
        "--force",
        "--exclude=scripts,externals",
        "--refresh-externals=never",
        "~/.bashrc",
    )
    assert cli.cat("a", Path("b")).argv == ("chezmoi", "--source", str(tmp_path), "cat", "a", "b")
    assert cli.diff("a", exclude="scripts").argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "diff",
        "--exclude=scripts",
        "a",
    )
    assert cli.init(apply=True, config_path=tmp_path / "cfg.toml", prompt_defaults=True, no_tty=True).argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "init",
        "--apply",
        "--config-path",
        str(tmp_path / "cfg.toml"),
        "--promptDefaults",
        "--no-tty",
    )
    assert cli.managed(include=("files", "scripts"), format="json", path_style="all").argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "managed",
        "--include=files,scripts",
        "--format=json",
        "--path-style=all",
    )
    assert cli.source_path("x").argv == ("chezmoi", "--source", str(tmp_path), "source-path", "x")
    assert cli.status("x", include="remove").argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "status",
        "--include=remove",
        "x",
    )
    assert cli.target_path("x").argv == ("chezmoi", "--source", str(tmp_path), "target-path", "x")
    assert cli.raw("doctor", "--no-network").argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "doctor",
        "--no-network",
    )


def test_execute_template_variants(tmp_path: Path) -> None:
    cli = ChezmoiCli(source=tmp_path)
    override = {"chezmoi": {"os": "linux"}}

    inline = cli.execute_template("{{ .chezmoi.os }}", with_stdin=True, override_data=override)
    assert inline.argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "execute-template",
        "--with-stdin",
        "--override-data",
        json.dumps(override),
        "{{ .chezmoi.os }}",
    )

    from_file = cli.execute_template(file=tmp_path / "t.tmpl", init=True, override_data='{"a": 1}')
    assert from_file.argv == (
        "chezmoi",
        "--source",
        str(tmp_path),
        "execute-template",
        "--file",
        "--init",
        "--override-data",
        '{"a": 1}',
        str(tmp_path / "t.tmpl"),
    )

    stdin_only = cli.execute_template()
    assert stdin_only.argv == ("chezmoi", "--source", str(tmp_path), "execute-template")


def test_validation_errors() -> None:
    with pytest.raises(ValueError, match="at least one target"):
        Cat(targets=())

    with pytest.raises(ValueError, match="either template or file"):
        ExecuteTemplate(template="{{ . }}", file=Path("a.tmpl"))


def test_functional_helpers_and_shell_formatting() -> None:
    cli = ChezmoiCli(source=Path("/my dir/src"))
    sub = Apply(targets=(Path("/my dir/file"),))

    assert build_argv(cli, sub) == ("chezmoi", "--source", "/my dir/src", "apply", "/my dir/file")
    assert format_command(cli, sub) == "chezmoi --source '/my dir/src' apply '/my dir/file'"
    assert cli.command(sub).shell == "chezmoi --source '/my dir/src' apply '/my dir/file'"


def test_run_sync_delegates_to_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(argv: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    monkeypatch.setattr("chezmoi_cli.cli.subprocess.run", fake_run)
    result = ChezmoiCli(source="/src").data(format="json").run(input="in", check=True, timeout=5)

    assert result.stdout == "ok"
    assert captured["argv"] == ("chezmoi", "--source", "/src", "data", "--format=json")
    assert captured["kwargs"] == {
        "input": "in",
        "env": None,
        "cwd": None,
        "capture_output": True,
        "text": True,
        "check": True,
        "timeout": 5,
    }


@pytest.mark.asyncio
async def test_run_async_delegates_to_asyncio_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    process = MagicMock()
    process.returncode = 0
    process.communicate = AsyncMock(return_value=(b"out", b"err"))
    process.wait = AsyncMock(return_value=0)
    create_exec = AsyncMock(return_value=process)

    monkeypatch.setattr("chezmoi_cli.cli.asyncio.create_subprocess_exec", create_exec)
    result = await ChezmoiCli(source="/src").execute_template("{{ . }}").run_async(input="stdin-text", timeout=10)

    assert result.returncode == 0
    assert result.stdout == "out"
    assert result.stderr == "err"
    create_exec.assert_awaited_once()
    process.communicate.assert_awaited_once_with(b"stdin-text")
