"""Unit tests for the guard helpers in cli/_common.py."""

from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
import typer

from sandboxr.cli._common import _apply_timeout, _require_srt


def _which(*, node_ok: bool, mise_ok: bool):
    def fn(name: str, **kwargs: object) -> str | None:
        if name == "node" and node_ok:
            return "/usr/bin/node"
        if name == "mise" and mise_ok:
            return "/usr/bin/mise"
        return None

    return fn


def test_require_srt_raises_when_node_missing() -> None:
    with (
        patch("shutil.which", side_effect=_which(node_ok=False, mise_ok=True)),
        pytest.raises(typer.Exit),
    ):
        _require_srt()


def test_require_srt_raises_when_mise_missing() -> None:
    with (
        patch("shutil.which", side_effect=_which(node_ok=True, mise_ok=False)),
        pytest.raises(typer.Exit),
    ):
        _require_srt()


def test_require_srt_raises_when_not_provisioned() -> None:
    def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args, 1, stdout="", stderr="not installed")

    with (
        patch("shutil.which", side_effect=_which(node_ok=True, mise_ok=True)),
        patch("sandboxr.backend.srt.subprocess.run", side_effect=_run),
        pytest.raises(typer.Exit),
    ):
        _require_srt()


def test_require_srt_passes_when_resolved(tmp_path: Path) -> None:
    install_dir = tmp_path / "npm-anthropic-ai-sandbox-runtime" / "0.0.63"
    cli_js = install_dir / "node_modules" / "@anthropic-ai" / "sandbox-runtime" / "dist" / "cli.js"
    cli_js.parent.mkdir(parents=True)
    cli_js.write_text("")

    def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args, 0, stdout=f"{install_dir}\n", stderr="")

    with (
        patch("shutil.which", side_effect=_which(node_ok=True, mise_ok=True)),
        patch("sandboxr.backend.srt.subprocess.run", side_effect=_run),
    ):
        _require_srt()


def test_apply_timeout_none_returns_args_unchanged() -> None:
    assert _apply_timeout(["bwrap", "--foo"], None) == ["bwrap", "--foo"]


def test_apply_timeout_prefixes_with_foreground_flag() -> None:
    with patch("shutil.which", return_value="/usr/bin/timeout"):
        result = _apply_timeout(["bwrap", "--foo"], 300)
    assert result == ["/usr/bin/timeout", "--foreground", "300", "bwrap", "--foo"]


def test_apply_timeout_raises_when_binary_missing() -> None:
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(typer.Exit),
    ):
        _apply_timeout(["bwrap", "--foo"], 300)
