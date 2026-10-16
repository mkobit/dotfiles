"""Ensure mise and editable local tools use the configured source checkout root."""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPOSITORY_ROOT / "src/chezmoi/.chezmoiscripts"
MISE_SCRIPT = SCRIPT_DIR / "run_onchange_after_07_trust-install-repo-mise-tools.sh.tmpl"
LOCAL_TOOLS_SCRIPT = SCRIPT_DIR / "run_onchange_after_08_install-local-bin-tools.sh.tmpl"


def _render(
    template: Path,
    *,
    source_root: Path | None = None,
    destination: Path | None = None,
    mise_method: str | None = "github_releases",
) -> subprocess.CompletedProcess[str]:
    data = {
        "local": {"bin": {"mise": {"installation_method": mise_method} if mise_method is not None else {}}},
        "local_bin_tools": {},
    }
    if source_root is not None:
        data["local_bin_tools_root"] = str(source_root)
        data["local_bin_tools"]["fixture"] = {
            "installation_method": "dotfiles.uv",
            "source_dir": "src/python/fixture",
        }
    else:
        data["local_bin_tools"]["termstatus"] = {
            "installation_method": "dotfiles.uv",
            "source_dir": "src/python/termstatus",
        }
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPOSITORY_ROOT),
            *(["--destination", str(destination)] if destination is not None else []),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(data),
            str(template),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def test_mise_and_editable_tool_use_configured_checkout_root(tmp_path):
    source_root = tmp_path / "base-checkout"
    source_root.mkdir()
    (source_root / "mise.toml").write_text("[tools]\n", encoding="utf-8")
    source_dirs = (
        "termstatus",
        "jules_cli",
        "transcribe",
        "termbud",
        "sandboxr",
        "browser_sync",
        "fixture",
    )
    for source_dir in source_dirs:
        project = source_root / "src/python" / source_dir
        project.mkdir(parents=True, exist_ok=True)
        (project / "pyproject.toml").write_text('[project]\nname = "fixture"\nversion = "0.1.0"\n', encoding="utf-8")

    mise = _render(MISE_SCRIPT, source_root=source_root)
    local_tools = _render(LOCAL_TOOLS_SCRIPT, source_root=source_root)

    assert mise.returncode == 0, mise.stderr
    assert local_tools.returncode == 0, local_tools.stderr
    assert f'mise trust "{source_root}/mise.toml"' in mise.stdout
    assert f'mise install -C "{source_root}"' in mise.stdout
    assert f'--cd "{source_root}"' in local_tools.stdout
    assert f'--editable "{source_root}/src/python/fixture"' in local_tools.stdout


def test_mise_and_editable_tool_default_to_standalone_working_tree():
    mise = _render(MISE_SCRIPT)
    local_tools = _render(LOCAL_TOOLS_SCRIPT)

    assert mise.returncode == 0, mise.stderr
    assert local_tools.returncode == 0, local_tools.stderr
    assert f'mise trust "{REPOSITORY_ROOT}/mise.toml"' in mise.stdout
    assert f'mise install -C "{REPOSITORY_ROOT}"' in mise.stdout
    assert f'--cd "{REPOSITORY_ROOT}"' in local_tools.stdout
    assert f'--editable "{REPOSITORY_ROOT}/src/python/termstatus"' in local_tools.stdout


@pytest.mark.parametrize("assembled", [False, True])
def test_legacy_tool_cleanup_uses_mise_at_base_checkout(tmp_path, assembled):
    source_root = tmp_path / "overlay/src/base" if assembled else None
    destination = tmp_path / "destination"
    local_bin = destination / ".local/bin"
    local_bin.mkdir(parents=True)
    trace = tmp_path / "mise-commands"
    mise = local_bin / "mise"
    mise.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$MISE_TEST_TRACE"\n'
        'test "$1" = exec && test "$2" = --cd && test -d "$3" || exit 1\n'
        'test "$4 $5 $6" = "-- uv tool" || exit 1\n'
        'if test "$7" = list; then printf "%s\\n" "tmux-helper v1" "tmux-runtime-tools v1"; fi\n',
        encoding="utf-8",
    )
    mise.chmod(0o755)
    if source_root is not None:
        source_root.mkdir(parents=True)
    script = _render(
        SCRIPT_DIR / "run_once_after_uninstall_tmux_helper.sh.tmpl", source_root=source_root, destination=destination
    )
    assert script.returncode == 0, script.stderr

    result = subprocess.run(
        ["bash"],
        input=script.stdout,
        env={**os.environ, "PATH": "/usr/bin:/bin", "MISE_TEST_TRACE": str(trace)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    root = source_root if assembled else REPOSITORY_ROOT
    commands = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    assert commands == [
        f"exec --cd {root} -- uv tool list",
        f"exec --cd {root} -- uv tool uninstall tmux-helper",
        f"exec --cd {root} -- uv tool list",
        f"exec --cd {root} -- uv tool uninstall tmux-runtime-tools",
    ]


@pytest.mark.parametrize("mise_method", [None, "none"])
def test_legacy_tool_cleanup_is_empty_when_mise_is_not_enabled(tmp_path, mise_method):
    script = _render(
        SCRIPT_DIR / "run_once_after_uninstall_tmux_helper.sh.tmpl", destination=tmp_path, mise_method=mise_method
    )

    assert script.returncode == 0, script.stderr
    assert script.stdout == ""


@pytest.mark.parametrize(
    ("mise_status", "expected_status"),
    [
        pytest.param(None, 127, id="missing-mise"),
        pytest.param(42, 42, id="failed-list"),
        pytest.param(0, 0, id="empty-list"),
    ],
)
def test_legacy_tool_cleanup_preserves_list_status(tmp_path, mise_status, expected_status):
    destination = tmp_path / "destination"
    local_bin = destination / ".local/bin"
    local_bin.mkdir(parents=True)
    trace = tmp_path / "mise-commands"
    if mise_status is not None:
        mise = local_bin / "mise"
        mise.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "$*" >> "$MISE_TEST_TRACE"\nexit {mise_status}\n',
            encoding="utf-8",
        )
        mise.chmod(0o755)
    script = _render(SCRIPT_DIR / "run_once_after_uninstall_tmux_helper.sh.tmpl", destination=destination)
    assert script.returncode == 0, script.stderr

    result = subprocess.run(
        ["bash"],
        input=script.stdout,
        env={**os.environ, "PATH": "/usr/bin:/bin", "MISE_TEST_TRACE": str(trace)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == expected_status, result.stderr
    commands = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    expected_calls = 0 if mise_status is None else 1 if mise_status else 2
    assert commands == [f"exec --cd {REPOSITORY_ROOT} -- uv tool list"] * expected_calls
