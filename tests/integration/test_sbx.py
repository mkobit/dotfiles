import json
import shutil
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
SBX_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / "sbx.toml"
CHEZMOI_REMOVE = CHEZMOI_SOURCE / ".chezmoiremove"
LEGACY_TARGETS = (
    ".local/bin/sbx-agy",
    ".local/bin/tools/sbx-agy",
    ".local/share/sbx/AGENTS.md",
    ".local/share/sbx/mixins/chezmoi-init/spec.yaml",
    ".local/share/sbx/mixins/git-config/files/home/.gitconfig",
    ".local/share/sbx/mixins/git-config/spec.yaml",
    ".local/share/sbx/mixins/mise/files/home/.config/mise/config.toml",
    ".local/share/sbx/mixins/mise/spec.yaml",
    ".local/share/sbx/sandboxes/agy/spec.yaml",
)


def test_sbx_release_catalog_pins_v0_39_0_with_verified_linux_checksums():
    """Keep the SBX release archive pinned to the verified v0.39.0 assets."""
    with SBX_CATALOG.open("rb") as catalog_file:
        catalog = tomllib.load(catalog_file)

    sbx = catalog["bin"]["sbx"]
    assert sbx["version"] == "0.39.0"
    assert sbx["github_releases"]["checksums"] == {
        "linux_amd64": "2ec45bc7938c20c2f406fe8cc72294ad5a954bdc047601484b89bf1a108311d4",
        "linux_arm64": "39c470a5f5e0991b1c2358952e2ab32a7b0309bfa57ac62b6bbc64b466d02c17",
    }


def test_sbx_does_not_manage_legacy_host_integration_targets():
    """Keep SBX limited to its binary rather than host-managed launchers or kits."""
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(CHEZMOI_SOURCE),
            "managed",
            "--include=files",
            "--format=json",
            "--path-style=all",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    managed_targets = json.loads(result.stdout)

    for target in LEGACY_TARGETS:
        assert target not in managed_targets


def test_sbx_legacy_targets_are_registered_for_chezmoi_removal():
    """Prune host files that were managed before the repository-local redesign."""
    remove_targets = CHEZMOI_REMOVE.read_text(encoding="utf-8")

    for target in LEGACY_TARGETS:
        assert target in remove_targets


def test_sbx_legacy_targets_are_pruned_without_deleting_user_sbx_data(tmp_path):
    """Ensure upgrades prune former managed files but retain user SBX data."""
    destination = tmp_path / "destination"
    destination.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(CHEZMOI_REMOVE, source / ".chezmoiremove")
    (source / ".chezmoi.toml").write_text('[data.zsh]\nprompt = "none"\n', encoding="utf-8")

    for target in LEGACY_TARGETS:
        path = destination / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    user_sbx_file = destination / ".local/share/sbx/user/keep.txt"
    user_sbx_file.parent.mkdir(parents=True)
    user_sbx_file.touch()

    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--config",
            str(source / ".chezmoi.toml"),
            "--destination",
            str(destination),
            "--cache",
            str(tmp_path / "cache"),
            "--persistent-state",
            str(tmp_path / "chezmoistate.boltdb"),
            "apply",
            "--force",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, f"chezmoi apply failed.\\nstderr: {result.stderr}\\nstdout: {result.stdout}"

    for target in LEGACY_TARGETS:
        assert not (destination / target).exists(), f"legacy target remains after apply: {target}"
    assert user_sbx_file.exists(), "migration removed unrelated user SBX data"
