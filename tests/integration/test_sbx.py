import json
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
SBX_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / "sbx.toml"
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
