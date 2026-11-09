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

from skill_filter import plugin_bridge

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
PLUGIN_BRIDGE_DATA = SOURCE_ROOT / ".chezmoidata/ai/plugin-bridge.toml"
MARKETPLACE_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_cursor-plugin/marketplace.json.tmpl"),
)
BRIDGE_TEMPLATE = Path(".chezmoitemplates/ai/plugin-bridge")
SUPERPOWERS_ARCHIVE_CONTENTS = {
    ".claude-plugin/plugin.json": b'{"name":"superpowers","version":"7.0.0"}\n',
    ".codex-plugin/plugin.json": b'{"name":"superpowers","version":"7.0.0"}\n',
    ".cursor-plugin/plugin.json": b'{"name":"superpowers","hooks":"./hooks/hooks-cursor.json"}\n',
    "hooks/hooks-cursor.json": b'{"version":1,"hooks":{"sessionStart":[]}}\n',
    "skills/using-superpowers/SKILL.md": b"# Upstream skill\n",
    "hooks/session-start": b"#!/bin/sh\nexit 0\n",
    "nested/AGENTS.md": b"# Upstream agents\n",
    "CLAUDE.md": b"# Upstream Claude context\n",
    "GEMINI.md": b"# Upstream Gemini context\n",
    ".gitignore": b"cache/\n",
    "BUILD": b"# Upstream build file\n",
    "rules/example.mdc": b"# Upstream rule\n",
    "tests/expected_fixture": b"Upstream test data\n",
    "test_data.toml": b'example = "upstream"\n',
}
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
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--cache",
            str(destination.parent / "cache"),
            "--persistent-state",
            str(destination.parent / "state.boltdb"),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        cwd=destination.parent,
        text=True,
    )


def _snapshot(destination: Path) -> dict[str, bytes]:
    roots = [
        destination / ".local/share/agent-plugins/marketplace",
        destination / ".local/share/agent-plugins/marketplaces",
        destination / ".cursor/plugins/local",
    ]
    return {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    }


def _upstream_fixture(
    tmp_path: Path,
    method: str | None,
    contents: dict[str, bytes],
    ignore_source: Path = SOURCE_ROOT,
    plugin: str = "superpowers",
) -> tuple[Path, Path, Path, dict[str, bytes]]:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    files = (
        *MARKETPLACE_TEMPLATES,
        BRIDGE_TEMPLATE,
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
        for name, content in contents.items():
            entry = tarfile.TarInfo(f"upstream-wrapper/{name}")
            entry.size = len(content)
            entry.mode = 0o755 if name == "hooks/session-start" else 0o644
            bundle.addfile(entry, io.BytesIO(content))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    config_lines = [
        f"[data.ai.plugins.{plugin}]",
        f'ref = "{"a" * 40}"',
        f'sha256 = "{checksum}"',
        *([] if method is None else [f"installation_method = {json.dumps(method)}"]),
        "[data.ai.skills.hosts.github]",
        f"url_format = {json.dumps(archive.as_uri())}",
        "[data.ai.skills.authored]",
        "[data.ai.agents.external]",
        "[data.local.bin.agy]",
        'installation_method = "github_releases"',
        "[data.mise.global_tools.bun]",
        'installation_method = "none"',
    ]
    config.write_text("\n".join(config_lines), encoding="utf-8")
    return source, destination, config, contents


@pytest.mark.parametrize("method", [None, "none", "chezmoi_external"])
def test_egm_gate_controls_complete_package_and_host_registrations(tmp_path, method):
    source, destination, config, contents = _upstream_fixture(tmp_path, method, EGM_ARCHIVE_CONTENTS, plugin="egm")
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
    rendered = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "execute-template",
            '{{ includeTemplate "ai/plugin-bridge" . }}',
        ],
        capture_output=True,
        check=False,
        text=True,
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
        } == contents
    first_snapshot = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    repeated = _apply(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == first_snapshot


@pytest.mark.parametrize("method", [None, "none"])
def test_egm_disabled_after_install_removes_package(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, "chezmoi_external", EGM_ARCHIVE_CONTENTS, plugin="egm")
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


def test_base_init_enables_egm(tmp_path):
    source, destination, config, _ = _upstream_fixture(tmp_path, None, EGM_ARCHIVE_CONTENTS, plugin="egm")
    fixture_config = config.read_text()
    shutil.copy2(SOURCE_ROOT / ".chezmoi.toml.tmpl", source / ".chezmoi.toml.tmpl")
    rendered = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--no-tty",
            "init",
        ],
        env={**os.environ, "CI": "true"},
        capture_output=True,
        check=False,
        text=True,
    )
    assert rendered.returncode == 0, rendered.stderr
    method = tomllib.loads(config.read_text())["data"]["ai"]["plugins"]["egm"]["installation_method"]
    config.write_text(
        fixture_config.replace(
            "[data.ai.plugins.egm]",
            f'[data.ai.plugins.egm]\ninstallation_method = "{method}"',
        )
    )
    applied = _apply(source, destination, config)
    assert applied.returncode == 0, applied.stderr
    assert (destination / ".local/share/agent-plugins/marketplaces/egm/plugins/egm").is_dir()


@pytest.mark.parametrize("method", [None, "none", "chezmoi_external"])
def test_upstream_plugin_gate_controls_marketplaces_and_registration(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, method, SUPERPOWERS_ARCHIVE_CONTENTS)
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    enabled = method == "chezmoi_external"
    marketplace_root = destination / ".local/share/agent-plugins/marketplace"
    superpowers_root = destination / ".local/share/agent-plugins/marketplaces/superpowers-marketplace"
    for host_path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        plugins = {entry["name"]: entry for entry in json.loads((marketplace_root / host_path).read_text())["plugins"]}
        assert "superpowers" not in plugins
        assert "mkobit-dotfiles" in plugins
        upstream = json.loads((superpowers_root / host_path).read_text())
        assert upstream["name"] == "superpowers-marketplace"
        plugins = {entry["name"]: entry for entry in upstream["plugins"]}
        assert ("superpowers" in plugins) == enabled
        assert "mkobit-dotfiles" not in plugins
        if enabled:
            declared_source = plugins["superpowers"]["source"]
            path = declared_source["path"] if isinstance(declared_source, dict) else declared_source
            assert path == "./plugins/superpowers"
    assert (superpowers_root / "plugins/superpowers").exists() == enabled
    assert (destination / ".cursor/plugins/local/superpowers").exists() == enabled

    runner = SOURCE_ROOT / ".chezmoiscripts/run_after_agent-plugin-bridge.sh.tmpl"
    rendered = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "execute-template",
        ],
        input=runner.read_text(),
        capture_output=True,
        check=False,
        text=True,
    )
    assert rendered.returncode == 0, rendered.stderr
    payload = json.loads(rendered.stdout.partition("<<'EOF'\n")[2].removesuffix("EOF\n"))
    assert ("superpowers" in payload["plugin_bridge"]["capabilities"]) == enabled
    assert ("superpowers-marketplace" in payload["plugin_bridge"]["marketplaces"]) == enabled
    if enabled:
        assert payload["plugin_bridge"]["capabilities"]["superpowers"]["package_path"] == "./plugins/superpowers"
        assert payload["plugin_bridge"]["marketplaces"]["superpowers-marketplace"]["source_locator"] == str(
            superpowers_root
        )
    provenance = json.loads((marketplace_root / "bridge-provenance.json").read_text())
    capabilities = {entry["name"]: entry for entry in provenance["capabilities"]}
    assert ("superpowers" in capabilities) == enabled
    assert capabilities["mkobit-dotfiles"]["upstream_sources"] == []
    if enabled:
        assert capabilities["superpowers"]["upstream_sources"][0]["name"] == "superpowers"
        assert capabilities["superpowers"]["marketplace"] == "superpowers-marketplace"


@pytest.mark.parametrize("ignore_layer", ["base", "overlay"])
@pytest.mark.parametrize(
    ("plugin", "archive_contents", "cursor"),
    [("superpowers", SUPERPOWERS_ARCHIVE_CONTENTS, True), ("egm", EGM_ARCHIVE_CONTENTS, False)],
)
def test_upstream_archive_preserves_files_and_prunes_old_skill_copies(
    tmp_path, ignore_layer, plugin, archive_contents, cursor
):
    overlay_source = REPOSITORY_ROOT.parent.parent / "src/chezmoi"
    if ignore_layer == "overlay" and not (overlay_source / ".chezmoiignore.tmpl").is_file():
        pytest.skip("the overlay ignore policy is not available in this checkout")
    source, destination, config, contents = _upstream_fixture(
        tmp_path,
        "chezmoi_external",
        archive_contents,
        SOURCE_ROOT if ignore_layer == "base" else overlay_source,
        plugin=plugin,
    )
    catalog = tomllib.loads((SOURCE_ROOT / f".chezmoidata/ai/plugins/{plugin}.toml").read_text())
    package = destination / catalog["ai"]["plugins"][plugin]["path"]
    for stale in (package / "stale.txt", package / "nested/stale.txt"):
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n")
    sentinel = destination / ".local/share/agent-plugins/runtime/sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep\n")
    legacy_package = destination / ".local/share/agent-plugins/marketplace/plugins/superpowers"
    legacy_package.mkdir(parents=True)
    (legacy_package / "legacy.txt").write_text("remove\n")
    # Dotfiles own the generated marketplace plugins/ folder, so an unknown plugin there goes.
    foreign_sibling = destination / ".local/share/agent-plugins/marketplace/plugins/custom-plugin"
    foreign_sibling.mkdir(parents=True)
    (foreign_sibling / "plugin.json").write_text('{"name":"custom-plugin"}\n')
    # Cursor local copies are replaced by run_onchange_after_agent-plugin-cursor-local, which this fixture omits.
    old_roots = (
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/skills",
        ".claude/skills",
        ".codex/skills",
        ".cursor/skills",
        ".gemini/antigravity-cli/skills",
    )
    for root in old_roots:
        old_skill = destination / root / "brainstorming/SKILL.md"
        old_skill.parent.mkdir(parents=True)
        old_skill.write_text("old skill\n")

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    installed_packages = [package]
    if cursor:
        installed_packages.append(destination / f".cursor/plugins/local/{plugin}")
    else:
        assert not (destination / f".cursor/plugins/local/{plugin}").exists()
    for installed in installed_packages:
        assert {
            path.relative_to(installed).as_posix(): path.read_bytes() for path in installed.rglob("*") if path.is_file()
        } == contents
        if "hooks/session-start" in contents:
            assert (installed / "hooks/session-start").stat().st_mode & 0o111
    assert sentinel.read_text() == "keep\n"
    for root in old_roots:
        assert not (destination / root / "brainstorming").exists()
    assert not legacy_package.exists()
    assert not foreign_sibling.exists()
    first_snapshot = _snapshot(destination)
    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(destination) == first_snapshot


@pytest.mark.parametrize("method", [None, "none"])
def test_upstream_plugin_disabled_after_install_removes_package(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, "chezmoi_external", SUPERPOWERS_ARCHIVE_CONTENTS)
    installed = _apply(source, destination, config)
    assert installed.returncode == 0, installed.stderr
    package = destination / ".local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers"
    cursor_package = destination / ".cursor/plugins/local/superpowers"
    assert package.is_dir()
    assert cursor_package.is_dir()
    sentinel = destination / ".cursor/plugins/local/custom/plugin.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text('{"name":"custom"}\n')
    config.write_text(
        config.read_text().replace(
            'installation_method = "chezmoi_external"',
            "" if method is None else 'installation_method = "none"',
        )
    )
    disabled = _apply(source, destination, config)
    assert disabled.returncode == 0, disabled.stderr
    assert not package.exists()
    assert not cursor_package.exists()
    assert sentinel.read_text() == '{"name":"custom"}\n'
    repeated = _apply(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert not cursor_package.exists()
    assert sentinel.read_text() == '{"name":"custom"}\n'
