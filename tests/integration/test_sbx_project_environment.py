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


@pytest.mark.parametrize(
    ("phase", "message"),
    [
        ("project", "The private guest workspace is required"),
        ("unknown", "Expected system or project installation phase"),
        ("", "Expected system or project installation phase"),
    ],
)
def test_packaged_bootstrap_rejects_invalid_input_without_side_effects(tmp_path, phase, message):
    package = _packaged_source(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    rejected = subprocess.run(
        ["/bin/sh", str(package / "install.sh"), phase],
        cwd=workspace,
        env={"PATH": ""},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert rejected.returncode == 2
    assert message in rejected.stderr
    assert not list(workspace.iterdir())
