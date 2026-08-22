import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SBX_DIR = REPO_ROOT / "src" / "sbx"
MIXINS_DIR = SBX_DIR / "mixins"
SANDBOXES_DIR = SBX_DIR / "sandboxes"


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
