import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
KIT_SOURCE = REPO_ROOT / ".sbx" / "kit"


def _packaged_source(tmp_path):
    """Copy only the kit source, without the repository or host workspace."""
    return Path(shutil.copytree(KIT_SOURCE, tmp_path / "kit"))


def test_private_clone_uses_immutable_native_workload():
    environment = yaml.safe_load((REPO_ROOT / ".sbx" / "sbxenv.yaml").read_text())
    assert environment["workspace"]["clone"] is True
    assert environment["workspace"]["path"] == ".."
    assert environment["agent"] == "sbx-kit-codex"
    workload, mixin = environment["kits"]
    assert re.fullmatch(r"docker.io/docker/sbx-kit-codex@sha256:[a-f0-9]{64}", workload)
    assert mixin == "./kit"
    assert "sandboxOptions" not in environment


def test_local_kit_packages_its_bootstrap(tmp_path):
    package = _packaged_source(tmp_path)
    spec = yaml.safe_load((package / "spec.yaml").read_text())
    assert spec["schemaVersion"] == "3"
    assert spec["kind"] == "mixin"
    recipe = (package / spec["dockerfile"]).read_text()
    assert "FROM scratch" in recipe
    assert not re.search(r"^(ENTRYPOINT|CMD|USER|WORKDIR)\b", recipe, re.MULTILINE)
    capabilities = {item["type"]: item["config"] for item in spec["capabilities"]}
    lifecycle = capabilities["com.docker.sandbox/lifecycle@1"]
    assert "interactive" not in lifecycle
    assert "com.docker.sandbox/sbx@1" not in capabilities
    for hook in lifecycle["install"]:
        command = hook["command"]
        assert command[:2] == ["sh", "/opt/dotfiles/install.sh"]
        assert "COPY install.sh /opt/dotfiles/install.sh" in recipe
        if command[-1] == "project":
            assert "WORKSPACE_DIR" in hook["env"]
    parsed = subprocess.run(["sh", "-n", str(package / "install.sh")], capture_output=True, text=True, check=False)
    assert parsed.returncode == 0, parsed.stderr
    assert "$WORKSPACE_DIR/.sbx" not in (package / "install.sh").read_text()


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.sbx", methods={"github_releases", "homebrew"})
def test_native_offline_packaged_kit_validation(tmp_path, host):
    sbx = shutil.which("sbx")
    assert sbx is not None, "SBX is enabled but absent"
    package = _packaged_source(tmp_path)
    validated = subprocess.run(
        [sbx, "kit", "validate", "--offline", str(package)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert validated.returncode == 0, f"{validated.stdout}\n{validated.stderr}"
