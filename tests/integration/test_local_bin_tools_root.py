"""Ensure mise and editable local tools use the configured source checkout root."""

import json
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPOSITORY_ROOT / "src/chezmoi/.chezmoiscripts"
MISE_SCRIPT = SCRIPT_DIR / "run_onchange_after_07_trust-install-repo-mise-tools.sh.tmpl"
LOCAL_TOOLS_SCRIPT = SCRIPT_DIR / "run_onchange_after_08_install-local-bin-tools.sh.tmpl"


def _render(template: Path, *, source_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    data = {
        "local": {"bin": {"mise": {"installation_method": "github_releases"}}},
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
