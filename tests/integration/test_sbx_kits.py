import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SBX_DIR = REPO_ROOT / "src" / "chezmoi" / "dot_local" / "share" / "sbx"
MIXINS_DIR = SBX_DIR / "mixins"
SANDBOXES_DIR = SBX_DIR / "sandboxes"
CHEZMOI_DATA_DIR = REPO_ROOT / "src" / "chezmoi" / ".chezmoidata"


def _render_template(template_path: Path) -> str:
    result = subprocess.run(
        ["chezmoi", "--source", str(REPO_ROOT / "src" / "chezmoi"), "execute-template", "-f", str(template_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _load_spec(kit_dir: Path) -> dict:
    spec_path = kit_dir / "spec.yaml"
    if not spec_path.is_file():
        spec_path = kit_dir / "spec.yaml.tmpl"
    assert spec_path.is_file(), f"Missing spec.yaml or spec.yaml.tmpl in {kit_dir}"

    if spec_path.suffix == ".tmpl":
        content = _render_template(spec_path)
    else:
        content = spec_path.read_text(encoding="utf-8")
        if "{{" in content:
            content = _render_template(spec_path)

    return yaml.safe_load(content)


def _render_kit_to_dir(kit_dir: Path, target_dir: Path) -> None:
    spec_tmpl = kit_dir / "spec.yaml.tmpl"
    spec_file = kit_dir / "spec.yaml"
    if spec_tmpl.is_file():
        rendered_spec = _render_template(spec_tmpl)
        (target_dir / "spec.yaml").write_text(rendered_spec, encoding="utf-8")
    elif spec_file.is_file():
        shutil.copy2(spec_file, target_dir / "spec.yaml")

    files_dir = kit_dir / "files"
    if files_dir.is_dir():
        for src_file in sorted(files_dir.rglob("*")):
            if not src_file.is_file():
                continue
            rel_path = src_file.relative_to(files_dir)
            transformed_parts = []
            for i, part in enumerate(rel_path.parts):
                if i == len(rel_path.parts) - 1:
                    name = part[:-5] if part.endswith(".tmpl") else part
                    name = f".{name[4:]}" if name.startswith("dot_") else name
                    transformed_parts.append(name)
                else:
                    transformed_parts.append(f".{part[4:]}" if part.startswith("dot_") else part)

            dest_file = target_dir / "files" / Path(*transformed_parts)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if src_file.suffix == ".tmpl":
                rendered_file = _render_template(src_file)
                dest_file.write_text(rendered_file, encoding="utf-8")
            else:
                shutil.copy2(src_file, dest_file)


def _find_kits(base_dir: Path) -> list[Path]:
    if not base_dir.is_dir():
        return []
    return [
        p
        for p in sorted(base_dir.iterdir())
        if p.is_dir() and ((p / "spec.yaml").is_file() or (p / "spec.yaml.tmpl").is_file())
    ]


MIXIN_KITS = _find_kits(MIXINS_DIR)
SANDBOX_KITS = _find_kits(SANDBOXES_DIR)
ALL_KITS = MIXIN_KITS + SANDBOX_KITS


def _validate_common_spec(spec: dict, kit_dir: Path):
    assert isinstance(spec, dict), f"spec.yaml in {kit_dir} must be a valid mapping"
    assert spec.get("schemaVersion") in ("1", "2"), f"Invalid schemaVersion in {kit_dir}"
    assert spec.get("name") == kit_dir.name, f"Kit name mismatch in {kit_dir}"

    if "environment" in spec and "variables" in spec["environment"]:
        vars_dict = spec["environment"]["variables"]
        assert isinstance(vars_dict, dict), f"environment.variables must be a dict in {kit_dir}"
        for k, v in vars_dict.items():
            assert isinstance(k, str) and isinstance(v, str), f"Variable {k} in {kit_dir} must be str:str"

    if "permissions" in spec and "network" in spec["permissions"]:
        allow_list = spec["permissions"]["network"].get("allow", [])
        assert isinstance(allow_list, list), f"permissions.network.allow must be a list in {kit_dir}"
        for endpoint in allow_list:
            assert isinstance(endpoint, str) and ":" in endpoint, f"Endpoint {endpoint} in {kit_dir} must be host:port"


@pytest.mark.parametrize("kit_dir", MIXIN_KITS, ids=lambda p: f"mixin-{p.name}")
def test_mixin_kit_structure_and_schema(kit_dir: Path):
    """Verify mixin kits contain valid spec.yaml manifests configured as mixins."""
    spec = _load_spec(kit_dir)
    _validate_common_spec(spec, kit_dir)
    assert spec.get("kind") == "mixin", f"Expected kind: mixin in {kit_dir}, got {spec.get('kind')}"


@pytest.mark.parametrize("kit_dir", SANDBOX_KITS, ids=lambda p: f"sandbox-{p.name}")
def test_sandbox_kit_structure_and_schema(kit_dir: Path):
    """Verify sandbox kits contain valid spec.yaml manifests configured as sandboxes."""
    spec = _load_spec(kit_dir)
    _validate_common_spec(spec, kit_dir)
    assert spec.get("kind") == "sandbox", f"Expected kind: sandbox in {kit_dir}, got {spec.get('kind')}"
    assert "sandbox" in spec, f"sandbox configuration block required in {kit_dir}"


def test_mise_mixin_version_parity():
    """Verify mise mixin version and tools match canonical chezmoidata definitions."""
    chezmoi_mise_file = CHEZMOI_DATA_DIR / "bin" / "mise.toml"
    assert chezmoi_mise_file.is_file(), f"Missing {chezmoi_mise_file}"

    with open(chezmoi_mise_file, "rb") as f:
        chezmoi_mise = tomllib.load(f)

    canonical_mise_version = chezmoi_mise["bin"]["mise"]["version"]
    canonical_global_tools = chezmoi_mise["mise"]["global_tools"]

    # Verify spec.yaml(.tmpl) version
    spec_file = MIXINS_DIR / "mise" / "spec.yaml.tmpl"
    if not spec_file.is_file():
        spec_file = MIXINS_DIR / "mise" / "spec.yaml"
    with open(spec_file, encoding="utf-8") as f:
        spec_text = f.read()

    assert "{{ .bin.mise.version }}" in spec_text or canonical_mise_version in spec_text

    # Verify config.toml(.tmpl) tools
    config_file = MIXINS_DIR / "mise" / "files" / "home" / "dot_config" / "mise" / "config.toml.tmpl"
    if not config_file.is_file():
        config_file = MIXINS_DIR / "mise" / "files" / "home" / ".config" / "mise" / "config.toml"
    assert config_file.is_file(), f"Missing {config_file}"

    with open(config_file, encoding="utf-8") as f:
        config_text = f.read()

    for tool_name in ["bun", "node", "pnpm", "python", "rust", "uv"]:
        assert tool_name in canonical_global_tools
        assert (
            f".mise.global_tools.{tool_name}.version" in config_text
            or canonical_global_tools[tool_name]["version"] in config_text
        )


def test_chezmoi_mixin_version_parity():
    """Verify chezmoi-init mixin version matches canonical CI/Jules workflow definitions."""
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), f"Missing {ci_file}"

    with open(ci_file, encoding="utf-8") as f:
        ci_yaml = yaml.safe_load(f)

    canonical_chezmoi_version = ci_yaml.get("env", {}).get("CHEZMOI_VERSION")
    assert canonical_chezmoi_version, f"Missing env.CHEZMOI_VERSION in {ci_file}"

    spec = _load_spec(MIXINS_DIR / "chezmoi-init")

    spec_env = spec.get("environment", {}).get("variables", {})
    assert spec_env.get("CHEZMOI_VERSION") == canonical_chezmoi_version, (
        f"CHEZMOI_VERSION in chezmoi-init ({spec_env.get('CHEZMOI_VERSION')}) "
        f"does not match CI workflow ({canonical_chezmoi_version})"
    )


@pytest.mark.parametrize("kit_dir", ALL_KITS, ids=lambda p: f"validate-{p.name}")
def test_sbx_kit_validate_cli(kit_dir: Path):
    """Run native sbx kit validate CLI if sbx is available on PATH."""
    sbx_bin = shutil.which("sbx")
    if not sbx_bin:
        pytest.skip("sbx CLI not installed on host PATH")

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_kit_dir = Path(tmp_dir) / kit_dir.name
        temp_kit_dir.mkdir(parents=True, exist_ok=True)
        _render_kit_to_dir(kit_dir, temp_kit_dir)

        result = subprocess.run(
            [sbx_bin, "kit", "validate", str(temp_kit_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"sbx kit validate failed for {kit_dir}:\n{result.stderr}\n{result.stdout}"
        assert "VALID" in result.stdout or "valid" in result.stdout.lower()
