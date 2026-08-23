import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SBX_DIR = REPO_ROOT / "src" / "sbx"
MIXINS_DIR = SBX_DIR / "mixins"
SANDBOXES_DIR = SBX_DIR / "sandboxes"
CHEZMOI_DATA_DIR = REPO_ROOT / "src" / "chezmoi" / ".chezmoidata"


def _find_kits(base_dir: Path) -> list[Path]:
    if not base_dir.is_dir():
        return []
    return [p for p in sorted(base_dir.iterdir()) if p.is_dir() and (p / "spec.yaml").is_file()]


MIXIN_KITS = _find_kits(MIXINS_DIR)
SANDBOX_KITS = _find_kits(SANDBOXES_DIR)
ALL_KITS = MIXIN_KITS + SANDBOX_KITS


@pytest.mark.parametrize("kit_dir", MIXIN_KITS, ids=lambda p: f"mixin-{p.name}")
def test_mixin_kit_structure_and_schema(kit_dir: Path):
    """Verify mixin kits contain valid spec.yaml manifests configured as mixins."""
    spec_path = kit_dir / "spec.yaml"
    assert spec_path.is_file(), f"Missing spec.yaml in {kit_dir}"

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    assert isinstance(spec, dict), f"spec.yaml in {kit_dir} must be a valid mapping"
    assert spec.get("schemaVersion") in ("1", "2"), f"Invalid schemaVersion in {kit_dir}"
    assert spec.get("kind") == "mixin", f"Expected kind: mixin in {kit_dir}, got {spec.get('kind')}"
    assert spec.get("name") == kit_dir.name, f"Kit name mismatch in {kit_dir}"


@pytest.mark.parametrize("kit_dir", SANDBOX_KITS, ids=lambda p: f"sandbox-{p.name}")
def test_sandbox_kit_structure_and_schema(kit_dir: Path):
    """Verify sandbox kits contain valid spec.yaml manifests configured as sandboxes."""
    spec_path = kit_dir / "spec.yaml"
    assert spec_path.is_file(), f"Missing spec.yaml in {kit_dir}"

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    assert isinstance(spec, dict), f"spec.yaml in {kit_dir} must be a valid mapping"
    assert spec.get("schemaVersion") in ("1", "2"), f"Invalid schemaVersion in {kit_dir}"
    assert spec.get("kind") == "sandbox", f"Expected kind: sandbox in {kit_dir}, got {spec.get('kind')}"
    assert spec.get("name") == kit_dir.name, f"Kit name mismatch in {kit_dir}"
    assert "sandbox" in spec, f"sandbox configuration block required in {kit_dir}"


def test_mise_mixin_version_parity():
    """Verify mise mixin version and tools match canonical chezmoidata definitions."""
    chezmoi_mise_file = CHEZMOI_DATA_DIR / "bin" / "mise.toml"
    assert chezmoi_mise_file.is_file(), f"Missing {chezmoi_mise_file}"

    with open(chezmoi_mise_file, "rb") as f:
        chezmoi_mise = tomllib.load(f)

    canonical_mise_version = chezmoi_mise["bin"]["mise"]["version"]
    canonical_global_tools = chezmoi_mise["mise"]["global_tools"]

    # Verify spec.yaml version
    spec_file = MIXINS_DIR / "mise" / "spec.yaml"
    with open(spec_file, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    spec_env = spec.get("environment", {}).get("variables", {})
    assert spec_env.get("MISE_VERSION") == canonical_mise_version, (
        f"MISE_VERSION in {spec_file} ({spec_env.get('MISE_VERSION')}) "
        f"does not match canonical {chezmoi_mise_file} ({canonical_mise_version})"
    )

    # Verify config.toml tools
    config_file = MIXINS_DIR / "mise" / "files" / "home" / ".config" / "mise" / "config.toml"
    assert config_file.is_file(), f"Missing {config_file}"

    with open(config_file, "rb") as f:
        mixin_config = tomllib.load(f)

    for tool_name, version in mixin_config.get("tools", {}).items():
        assert tool_name in canonical_global_tools, f"Tool {tool_name} in mixin not found in canonical catalog"
        assert canonical_global_tools[tool_name]["version"] == version, (
            f"Version mismatch for {tool_name}: mixin has {version}, canonical has {canonical_global_tools[tool_name]['version']}"
        )


@pytest.mark.parametrize("kit_dir", ALL_KITS, ids=lambda p: f"validate-{p.name}")
def test_sbx_kit_validate_cli(kit_dir: Path):
    """Run native sbx kit validate CLI if sbx is available on PATH."""
    sbx_bin = shutil.which("sbx")
    if not sbx_bin:
        pytest.skip("sbx CLI not installed on host PATH")

    result = subprocess.run(
        [sbx_bin, "kit", "validate", str(kit_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"sbx kit validate failed for {kit_dir}:\n{result.stderr}\n{result.stdout}"
    assert "VALID" in result.stdout or "valid" in result.stdout.lower()
