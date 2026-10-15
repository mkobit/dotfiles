"""Verify environment-scoped capabilities in composed chezmoi fixtures."""

import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
AUTHORED_CAPABILITIES_EXTERNAL = SOURCE_ROOT / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl"
PLUGIN_BRIDGE_DATA = SOURCE_ROOT / ".chezmoidata/ai/plugin-bridge.toml"
MARKETPLACE_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
)
BRIDGE_TEMPLATE = Path(".chezmoitemplates/ai/plugin-bridge")


def _write_fixture_source(source: Path, repo_root: Path, config: Path, environment: str) -> None:
    (source / ".chezmoiexternals").mkdir(parents=True)
    shutil.copy2(
        AUTHORED_CAPABILITIES_EXTERNAL,
        source / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl",
    )
    data_file = source / ".chezmoidata/ai/plugin-bridge.toml"
    data_file.parent.mkdir(parents=True)
    shutil.copy2(PLUGIN_BRIDGE_DATA, data_file)

    for relative_path in (*MARKETPLACE_TEMPLATES, BRIDGE_TEMPLATE):
        target_file = source / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative_path, target_file)

    capabilities = {
        "mydev-capability": "mydev",
        "mydata-capability": "mydata",
    }
    config_lines = [
        "[data.ai.plugin_bridge]",
        f"environment = {json.dumps(environment)}",
        "",
    ]
    for capability, enabled_environment in capabilities.items():
        skill = repo_root / "src/overlay-plugins" / capability / "skills/example/SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(f"# {capability}\n", encoding="utf-8")
        config_lines.extend(
            [
                f"[data.ai.plugin_bridge.capabilities.{capability}]",
                f'description = "Fixture capability for {enabled_environment}."',
                f'source_dir = "src/overlay-plugins/{capability}"',
                'marketplace = "dotfiles"',
                'hosts = ["claude", "codex", "cursor"]',
                f"environments = [{json.dumps(enabled_environment)}]",
                "",
                f"[data.ai.plugin_bridge.capabilities.{capability}.skills]",
                'example = "present"',
                "",
            ]
        )
    config.write_text("\n".join(config_lines), encoding="utf-8")


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
        destination / ".cursor/plugins/local/mydev-capability",
        destination / ".cursor/plugins/local/mydata-capability",
        destination / ".cursor/plugins/local/superpowers",
    ]
    return {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("environment", "selected", "absent"),
    [
        ("mydev", "mydev-capability", "mydata-capability"),
        ("mydata", "mydata-capability", "mydev-capability"),
    ],
)
def test_environment_fixture_selects_capability_and_cursor_projection(tmp_path, environment, selected, absent):
    """The selected environment gets its marketplace entry and fresh Cursor skill projection."""
    repo_root = tmp_path / "repo"
    source = repo_root / "src/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    _write_fixture_source(source, repo_root, config, environment)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr

    claude_marketplace = destination / ".local/share/agent-plugins/marketplace/.claude-plugin/marketplace.json"
    codex_marketplace = destination / ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json"
    claude_names = {plugin["name"] for plugin in json.loads(claude_marketplace.read_text())["plugins"]}
    codex_names = {plugin["name"] for plugin in json.loads(codex_marketplace.read_text())["plugins"]}
    expected_names = {"mkobit-dotfiles", selected}
    assert claude_names == expected_names
    assert codex_names == expected_names

    selected_skill = destination / ".cursor/plugins/local" / selected / "skills/example/SKILL.md"
    absent_skill = destination / ".cursor/plugins/local" / absent / "skills/example/SKILL.md"
    assert selected_skill.read_text(encoding="utf-8") == f"# {selected}\n"
    assert not absent_skill.exists()

    first_snapshot = _snapshot(destination)
    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(destination) == first_snapshot


def _upstream_fixture(
    tmp_path: Path, method: str | None, ignore_source: Path = SOURCE_ROOT
) -> tuple[Path, Path, Path, dict[str, bytes]]:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    files = (
        *MARKETPLACE_TEMPLATES,
        BRIDGE_TEMPLATE,
        Path(".chezmoidata/ai/plugin-bridge.toml"),
        Path(".chezmoidata/ai/plugins/superpowers.toml"),
        Path(".chezmoidata/ai/skills/superpowers.toml"),
        Path(".chezmoiexternals/ai-upstream-plugins.toml.tmpl"),
        Path("dot_local/share/agent-plugins/marketplace/bridge-provenance.json.tmpl"),
        Path("dot_local/share/agent-plugins/.chezmoiremove.tmpl"),
        Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/.chezmoiremove.tmpl"),
        Path("dot_cursor/plugins/local/mkobit-dotfiles/.chezmoiremove.tmpl"),
        Path("dot_claude/.chezmoiremove.tmpl"),
        Path("dot_codex/.chezmoiremove.tmpl"),
        Path("dot_cursor/.chezmoiremove.tmpl"),
        Path("dot_gemini/.chezmoiremove.tmpl"),
        Path(".chezmoitemplates/ai/authored-plugin-manifest-ignore"),
        Path(".chezmoitemplates/python/filter-interpreter"),
    )
    for relative in files:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, target)
    shutil.copy2(ignore_source / ".chezmoiignore.tmpl", source / ".chezmoiignore.tmpl")
    resolver = source.parent / "python/skill_filter/resolve-interpreter.sh"
    resolver.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh", resolver)

    contents = {
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
    archive = tmp_path / "upstream.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for name, content in contents.items():
            entry = tarfile.TarInfo(f"upstream-wrapper/{name}")
            entry.size = len(content)
            entry.mode = 0o755 if name == "hooks/session-start" else 0o644
            bundle.addfile(entry, io.BytesIO(content))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    config_lines = [
        "[data.ai.plugins.superpowers]",
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
def test_upstream_plugin_gate_controls_marketplaces_and_registration(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, method)
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    enabled = method == "chezmoi_external"
    marketplace_root = destination / ".local/share/agent-plugins/marketplace"
    for host_path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        plugins = {entry["name"]: entry for entry in json.loads((marketplace_root / host_path).read_text())["plugins"]}
        assert ("superpowers" in plugins) == enabled
        assert "mkobit-dotfiles" in plugins
        if enabled:
            declared_source = plugins["superpowers"]["source"]
            path = declared_source["path"] if isinstance(declared_source, dict) else declared_source
            assert path == "./plugins/superpowers"
    assert (marketplace_root / "plugins/superpowers").exists() == enabled
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
    if enabled:
        assert payload["plugin_bridge"]["capabilities"]["superpowers"]["package_path"] == "./plugins/superpowers"
    provenance = json.loads((marketplace_root / "bridge-provenance.json").read_text())
    capabilities = {entry["name"]: entry for entry in provenance["capabilities"]}
    assert ("superpowers" in capabilities) == enabled
    assert capabilities["mkobit-dotfiles"]["upstream_sources"] == []
    if enabled:
        assert capabilities["superpowers"]["upstream_sources"][0]["name"] == "superpowers"


@pytest.mark.parametrize("ignore_layer", ["base", "overlay"])
def test_upstream_archive_preserves_files_and_prunes_old_skill_copies(tmp_path, ignore_layer):
    overlay_source = REPOSITORY_ROOT.parent.parent / "src/chezmoi"
    if ignore_layer == "overlay" and not (overlay_source / ".chezmoiignore.tmpl").is_file():
        pytest.skip("the overlay ignore policy is not available in this checkout")
    source, destination, config, contents = _upstream_fixture(
        tmp_path,
        "chezmoi_external",
        SOURCE_ROOT if ignore_layer == "base" else overlay_source,
    )
    package = destination / ".local/share/agent-plugins/marketplace/plugins/superpowers"
    for stale in (package / "stale.txt", package / "nested/stale.txt"):
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n")
    sentinel = destination / ".local/share/agent-plugins/runtime/sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep\n")
    old_roots = (
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/skills",
        ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/skills",
        ".cursor/plugins/local/mkobit-dotfiles/skills",
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
    for installed in (package, destination / ".cursor/plugins/local/superpowers"):
        assert {
            path.relative_to(installed).as_posix(): path.read_bytes() for path in installed.rglob("*") if path.is_file()
        } == contents
        assert (installed / "hooks/session-start").stat().st_mode & 0o111
    assert sentinel.read_text() == "keep\n"
    for root in old_roots:
        assert not (destination / root / "brainstorming").exists()
    first_snapshot = _snapshot(destination)
    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(destination) == first_snapshot


@pytest.mark.parametrize("method", [None, "none"])
def test_upstream_plugin_disabled_after_install_removes_package(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, "chezmoi_external")
    installed = _apply(source, destination, config)
    assert installed.returncode == 0, installed.stderr
    package = destination / ".local/share/agent-plugins/marketplace/plugins/superpowers"
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
