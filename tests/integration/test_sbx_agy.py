import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
SBX_AGY_SOURCE = CHEZMOI_SOURCE / "dot_local" / "bin" / "tools" / "executable_sbx-agy.tmpl"
SBX_AGY_TEMPLATE_DATA = '{"local":{"bin":{"sbx":{"installation_method":"github_releases"}}}}'


def _render() -> str:
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(CHEZMOI_SOURCE),
            "--refresh-externals=never",
            "--override-data",
            SBX_AGY_TEMPLATE_DATA,
            "execute-template",
            "-f",
            str(SBX_AGY_SOURCE),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout


def test_sbx_agy_is_a_clone_mode_launcher():
    assert SBX_AGY_SOURCE.is_file(), f"Missing {SBX_AGY_SOURCE}"
    rendered = _render()

    assert rendered.startswith("#!/usr/bin/env bash\n")
    for anchor in (
        "run --clone",
        "ls --quiet",
        "sandbox name is already in use",
        "files/home/.gemini/config/skills",
        "sandbox-$sandbox_name",
        "mktemp -d",
        "trap cleanup_staged_kit EXIT",
    ):
        assert anchor in rendered


def test_sbx_agy_does_not_grant_delivery_or_host_key_access():
    assert SBX_AGY_SOURCE.is_file(), f"Missing {SBX_AGY_SOURCE}"
    rendered = _render()

    for forbidden in ("--secret", "git push", "gh pr", "SSH_AUTH_SOCK", "GPG_AGENT_INFO"):
        assert forbidden not in rendered


def test_sbx_agy_validates_project_mixins_without_credentials():
    rendered = _render()

    for anchor in (
        "kit validate",
        "kit inspect",
        "project kit must not request credentials",
        '"credentials"',
    ):
        assert anchor in rendered


def _write_launcher(tmp_path: Path) -> tuple[Path, Path]:
    sbx_root = tmp_path / "sbx"
    (sbx_root / "sandboxes" / "agy").mkdir(parents=True)
    (sbx_root / "sandboxes" / "agy" / "spec.yaml").write_text(
        'schemaVersion: "2"\nkind: sandbox\nname: agy\n', encoding="utf-8"
    )
    (sbx_root / "mixins" / "mise").mkdir(parents=True)
    (sbx_root / "mixins" / "git-config").mkdir(parents=True)

    sbx_stub = tmp_path / "sbx-cli"
    sbx_stub.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >>"$SBX_LOG"
case "${1:-}" in
    ls)
        printf '%s\\n' "${SBX_LS_NAME:-}"
        ;;
    kit)
        case "${2:-}" in
            validate)
                ;;
            inspect)
                printf '%s\\n' "${SBX_INSPECTION:?missing SBX_INSPECTION}"
                ;;
        esac
        ;;
    run)
        ;;
esac
""",
        encoding="utf-8",
    )
    sbx_stub.chmod(0o755)

    git_stub = tmp_path / "git"
    git_stub.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${3:-}" == "rev-parse" && "${4:-}" == "--show-toplevel" ]]; then
    printf '%s\\n' "$2"
fi
""",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)

    rendered = _render()
    rendered = re.sub(r'^sbx_bin=".*"$', f'sbx_bin="{sbx_stub}"', rendered, flags=re.MULTILINE)
    rendered = re.sub(r'^sbx_root=".*"$', f'sbx_root="{sbx_root}"', rendered, flags=re.MULTILINE)
    rendered = re.sub(r'^host_skills=".*"$', f'host_skills="{tmp_path / "no-skills"}"', rendered, flags=re.MULTILINE)
    launcher = tmp_path / "sbx-agy"
    launcher.write_text(rendered, encoding="utf-8")
    launcher.chmod(0o755)
    return launcher, sbx_stub


def _run_launcher(
    launcher: Path,
    project: Path,
    *,
    name: str,
    log_path: Path,
    inspection: str = '{"manifest": {"kind": "mixin"}}',
    listed_name: str = "",
) -> subprocess.CompletedProcess[str]:
    env = os.environ | {
        "PATH": f"{launcher.parent}:{os.environ['PATH']}",
        "SBX_INSPECTION": inspection,
        "SBX_LOG": str(log_path),
        "SBX_LS_NAME": listed_name,
    }
    return subprocess.run(
        [str(launcher), "--name", name, str(project)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_sbx_agy_rejects_an_existing_name_before_run(tmp_path: Path):
    launcher, _ = _write_launcher(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    log_path = tmp_path / "sbx.log"

    result = _run_launcher(launcher, project, name="existing", log_path=log_path, listed_name="existing")

    assert result.returncode == 2
    assert "sandbox name is already in use" in result.stderr
    assert "run" not in log_path.read_text(encoding="utf-8").splitlines()


def test_sbx_agy_rejects_a_credential_bearing_project_mixin_before_run(tmp_path: Path):
    launcher, _ = _write_launcher(tmp_path)
    project = tmp_path / "project"
    project_kit = project / ".sbx" / "sbx-agy"
    project_kit.mkdir(parents=True)
    (project_kit / "spec.yaml").write_text('schemaVersion: "2"\nkind: mixin\nname: project\n', encoding="utf-8")
    log_path = tmp_path / "sbx.log"

    result = _run_launcher(
        launcher,
        project,
        name="credential-mixin",
        log_path=log_path,
        inspection='{"manifest": {"kind": "mixin"}, "credentials": [{"service": "github"}]}',
    )

    assert result.returncode == 2
    assert "project kit must not request credentials" in result.stderr
    assert "run" not in log_path.read_text(encoding="utf-8").splitlines()


def test_sbx_agy_runs_a_valid_mixin_in_clone_mode(tmp_path: Path):
    launcher, _ = _write_launcher(tmp_path)
    project = tmp_path / "project"
    project_kit = project / ".sbx" / "sbx-agy"
    project_kit.mkdir(parents=True)
    (project_kit / "spec.yaml").write_text('schemaVersion: "2"\nkind: mixin\nname: project\n', encoding="utf-8")
    log_path = tmp_path / "sbx.log"

    result = _run_launcher(launcher, project, name="valid-mixin", log_path=log_path)

    assert result.returncode == 0, result.stderr
    assert any(
        line.startswith("run --clone --name valid-mixin") for line in log_path.read_text(encoding="utf-8").splitlines()
    )
