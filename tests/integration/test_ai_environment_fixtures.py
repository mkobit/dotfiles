"""Verify environment-scoped capabilities in composed chezmoi fixtures."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

from chezmoi_cli import ChezmoiCli
from skill_filter import plugin_bridge

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
MARKETPLACE_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_cursor-plugin/marketplace.json.tmpl"),
)
EGM_ARCHIVE_CONTENTS = {
    ".claude-plugin/plugin.json": b'{"name":"egm","version":"0.1.1"}\n',
    ".codex-plugin/plugin.json": b'{"name":"egm","version":"0.1.1","skills":"./skills/"}\n',
    "plugin.json": b'{"name":"egm","version":"0.1.1"}\n',
    "skills/egm-review/SKILL.md": b"# Read ../../agents/design_critic.md\n",
    "agents/design_critic.md": b"# Read-only reviewer\n",
    "resources/document_standards/design-standard.md": b"# Design standard\n",
    "docs/codex.md": b"# Codex instructions\n",
    "nested/AGENTS.md": b"# Upstream agents\n",
    "CLAUDE.md": b"# Upstream Claude context\n",
    "GEMINI.md": b"# Upstream Gemini context\n",
    ".gitignore": b"cache/\n",
    "BUILD": b"# Upstream build file\n",
    "rules/example.mdc": b"# Upstream rule\n",
    "tests/expected_fixture": b"Upstream test data\n",
    "test_data.toml": b'example = "upstream"\n',
}


def _apply(source: Path, destination: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return (
        ChezmoiCli(
            source=source,
            destination=destination,
            config=config,
            cache=destination.parent / "cache",
            persistent_state=destination.parent / "state.boltdb",
            refresh_externals="always",
        )
        .apply()
        .run(cwd=destination.parent)
    )


def _egm_fixture(
    tmp_path: Path, method: str | None, *, ignore_source: Path = SOURCE_ROOT, agy_method: str = "github_releases"
) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    files = (
        *MARKETPLACE_TEMPLATES,
        Path(".chezmoidata/ai/plugin-bridge.toml"),
        Path(".chezmoidata/ai/skills/superpowers.toml"),
        Path(".chezmoiexternals/ai-upstream-plugins.toml.tmpl"),
        Path("dot_local/share/agent-plugins/marketplace/bridge-provenance.json.tmpl"),
        Path("dot_local/share/agent-plugins/.chezmoiremove.tmpl"),
        Path("dot_claude/.chezmoiremove.tmpl"),
        Path("dot_codex/.chezmoiremove.tmpl"),
        Path("dot_cursor/.chezmoiremove.tmpl"),
        Path("dot_gemini/.chezmoiremove.tmpl"),
        Path(".chezmoitemplates/python/filter-interpreter"),
    )
    for relative in files:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, target)
    for relative in (
        Path(".chezmoitemplates/ai"),
        Path(".chezmoidata/ai/plugins"),
        Path("dot_local/share/agent-plugins/marketplaces"),
        Path("dot_local/share/agent-plugins/marketplace/exact_plugins"),
    ):
        shutil.copytree(SOURCE_ROOT / relative, source / relative, dirs_exist_ok=True)
    shutil.copy2(ignore_source / ".chezmoiignore.tmpl", source / ".chezmoiignore.tmpl")
    resolver = source.parent / "python/skill_filter/resolve-interpreter.sh"
    resolver.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh", resolver)

    archive = tmp_path / "upstream.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for name, content in EGM_ARCHIVE_CONTENTS.items():
            entry = tarfile.TarInfo(f"upstream-wrapper/{name}")
            entry.size = len(content)
            bundle.addfile(entry, io.BytesIO(content))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    config_lines = [
        "[data.ai.plugins.egm]",
        f'ref = "{"a" * 40}"',
        f'sha256 = "{checksum}"',
        *([] if method is None else [f"installation_method = {json.dumps(method)}"]),
        "[data.ai.skills.hosts.github]",
        f"url_format = {json.dumps(archive.as_uri())}",
        "[data.ai.skills.authored]",
        "[data.ai.agents.external]",
        "[data.local.bin.agy]",
        f"installation_method = {json.dumps(agy_method)}",
        "[data.mise.global_tools.bun]",
        'installation_method = "none"',
    ]
    config.write_text("\n".join(config_lines), encoding="utf-8")
    return source, destination, config


@pytest.mark.parametrize("method", [None, "none", "chezmoi_external"])
def test_egm_gate_controls_complete_package_and_host_registrations(tmp_path, method):
    source, destination, config = _egm_fixture(tmp_path, method)
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    enabled = method == "chezmoi_external"
    root = destination / ".local/share/agent-plugins/marketplaces/egm"
    package = root / "plugins/egm"
    assert package.exists() == enabled
    assert not (destination / ".cursor/plugins/local/egm").exists()
    for host_path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        marketplace = json.loads((root / host_path).read_text())
        assert marketplace["name"] == "egm"
        assert [entry["name"] for entry in marketplace["plugins"]] == (["egm"] if enabled else [])
        if enabled:
            declared_source = marketplace["plugins"][0]["source"]
            path = declared_source["path"] if isinstance(declared_source, dict) else declared_source
            assert path == "./plugins/egm"
    rendered = (
        ChezmoiCli(source=source, destination=destination, config=config)
        .execute_template('{{ includeTemplate "ai/plugin-bridge" . }}')
        .run()
    )
    assert rendered.returncode == 0, rendered.stderr
    bridge = json.loads(rendered.stdout)
    assert ("egm" in bridge["capabilities"]) == enabled
    assert ("egm" in bridge["marketplaces"]) == enabled
    desired_agy = plugin_bridge._desired_agy_plugins(bridge["marketplaces"], destination)
    assert ("egm" in desired_agy) == enabled
    if enabled:
        assert bridge["capabilities"]["egm"]["hosts"] == ["claude", "codex", "antigravity"]
        assert bridge["marketplaces"]["egm"]["trust_class"] == "upstream"
        assert desired_agy["egm"] == ("egm", package, "0.1.1")
        assert {
            path.relative_to(package).as_posix(): path.read_bytes() for path in package.rglob("*") if path.is_file()
        } == EGM_ARCHIVE_CONTENTS
    first_snapshot = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    repeated = _apply(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == first_snapshot


@pytest.mark.parametrize("method", [None, "none"])
def test_egm_disabled_after_install_removes_package(tmp_path, method):
    source, destination, config = _egm_fixture(tmp_path, "chezmoi_external")
    installed = _apply(source, destination, config)
    assert installed.returncode == 0, installed.stderr
    package = destination / ".local/share/agent-plugins/marketplaces/egm/plugins/egm"
    assert package.is_dir()
    sentinel = destination / ".local/share/agent-plugins/runtime/sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep\n")
    config.write_text(
        config.read_text().replace(
            'installation_method = "chezmoi_external"',
            "" if method is None else 'installation_method = "none"',
        )
    )
    disabled = _apply(source, destination, config)
    assert disabled.returncode == 0, disabled.stderr
    assert not package.exists()
    assert sentinel.read_text() == "keep\n"


def test_base_init_selects_upstream_plugins(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    shutil.copy2(SOURCE_ROOT / ".chezmoi.toml.tmpl", source / ".chezmoi.toml.tmpl")
    rendered = (
        ChezmoiCli(source=source, destination=destination, config=config, no_tty=True)
        .init()
        .run(env={**os.environ, "CI": "true"})
    )
    assert rendered.returncode == 0, rendered.stderr
    plugins = tomllib.loads(config.read_text())["data"]["ai"]["plugins"]
    assert plugins["egm"]["installation_method"] == "chezmoi_external"
    assert "superpowers" not in plugins


@pytest.mark.parametrize("agy_method", ["github_releases", "none"])
def test_superpowers_migration_with_stale_install_config(tmp_path, agy_method):
    source, destination, config = _egm_fixture(tmp_path, None, agy_method=agy_method)
    with config.open("a", encoding="utf-8") as stream:
        stream.write("""
[data.ai.plugins.superpowers]
installation_method = "chezmoi_external"
[data.ai.plugin_bridge.marketplaces.superpowers-marketplace]
external_source = "superpowers"
hosts = ["claude", "codex", "antigravity"]
[data.ai.plugin_bridge.capabilities.superpowers]
marketplace = "superpowers-marketplace"
external_source = "superpowers"
hosts = ["claude", "codex"]
""")

    def chezmoi(*args: str) -> str:
        result = (
            ChezmoiCli(
                source=source,
                destination=destination,
                config=config,
                cache=tmp_path / "cache",
                persistent_state=tmp_path / "state.boltdb",
            )
            .raw(*args)
            .run()
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    externals = source / ".chezmoiexternals/ai-upstream-plugins.toml.tmpl"
    assert tomllib.loads(chezmoi("execute-template", externals.read_text())) == {}

    marketplace = Path(".local/share/agent-plugins/marketplaces/superpowers-marketplace")
    retired_paths = (
        marketplace / "plugins/superpowers",
        Path(".local/share/agent-plugins/marketplace/plugins/superpowers"),
        Path(".cursor/plugins/local/superpowers"),
        Path(".claude/skills/brainstorming"),
        Path(".codex/skills/brainstorming"),
        Path(".cursor/skills/brainstorming"),
        Path(".gemini/antigravity-cli/skills/brainstorming"),
    )
    other_paths = (Path(".cursor/plugins/local/custom"), Path(".gemini/antigravity-cli/skills/custom"))
    for path in (*retired_paths, *other_paths):
        (destination / path).mkdir(parents=True)
        (destination / path / "sentinel").touch()
    removed = set(chezmoi("status", "--include=remove").splitlines())
    assert {f" D {path}" for path in retired_paths} <= removed
    assert all(f" D {path}" not in removed for path in other_paths)

    for manifest in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
        rendered = json.loads(chezmoi("cat", str(destination / marketplace / manifest)))
        assert rendered["name"] == "superpowers-marketplace"
        assert rendered["plugins"] == []

    bridge = json.loads(chezmoi("execute-template", '{{ includeTemplate "ai/plugin-bridge" . }}'))
    assert "superpowers" not in bridge["capabilities"]
    retired = bridge["marketplaces"]["superpowers-marketplace"]
    assert retired["source_type"] == "generated"
    assert retired["hosts"] == []
    assert bridge["marketplaces"]["dotfiles"]["hosts"] == ["claude", "codex", "cursor", "antigravity"]
    assert bridge["cli_hosts"] == ([] if agy_method == "none" else ["antigravity"])

    for attempt in (1, 2):
        applied = _apply(source, destination, config)
        assert applied.returncode == 0, f"Apply {attempt}: {applied.stderr}"
        remaining = [path for path in retired_paths if os.path.lexists(destination / path)]
        assert not remaining, f"Apply {attempt} left retired paths: {remaining}"
        assert all((destination / path / "sentinel").is_file() for path in other_paths)


@pytest.mark.parametrize("ignore_layer", ["base", "overlay"])
def test_egm_archive_preserves_files_and_removes_stale_files(tmp_path, ignore_layer):
    overlay_source = REPOSITORY_ROOT.parent.parent / "src/chezmoi"
    if ignore_layer == "overlay" and not (overlay_source / ".chezmoiignore.tmpl").is_file():
        pytest.skip("the overlay ignore policy is not available in this checkout")
    source, destination, config = _egm_fixture(
        tmp_path,
        "chezmoi_external",
        ignore_source=SOURCE_ROOT if ignore_layer == "base" else overlay_source,
    )
    package = destination / ".local/share/agent-plugins/marketplaces/egm/plugins/egm"
    for stale in (package / "stale.txt", package / "nested/stale.txt"):
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n")

    applied = _apply(source, destination, config)
    assert applied.returncode == 0, applied.stderr
    assert {
        path.relative_to(package).as_posix(): path.read_bytes() for path in package.rglob("*") if path.is_file()
    } == EGM_ARCHIVE_CONTENTS
