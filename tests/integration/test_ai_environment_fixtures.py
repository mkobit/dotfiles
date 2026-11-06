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
PLUGIN_BRIDGE_DATA = SOURCE_ROOT / ".chezmoidata/ai/plugin-bridge.toml"
MARKETPLACE_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplaces/superpowers-marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplaces/superpowers-marketplace/dot_agents/plugins/marketplace.json.tmpl"),
    Path(".chezmoitemplates/ai/plugin-marketplace"),
    # ai/plugin-bridge reads the effective mkobit-dotfiles hosts from ai/agent-sources.
    Path(".chezmoitemplates/ai/agent-sources"),
    Path(".chezmoitemplates/ai/retired-skills"),
)
BRIDGE_TEMPLATE = Path(".chezmoitemplates/ai/plugin-bridge")


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


def _environment_fixture(fixture, environment: str, extra: str = "") -> None:
    """Write two environment-scoped plugins and a shared plugin with a mydata skill exclusion."""
    for name, enabled in (("mydev-capability", "mydev"), ("mydata-capability", "mydata")):
        fixture.write_plugin(name, skills={"example": {"SKILL.md": f"# {name}\n"}})
        extra += f'[data.ai.plugin_bridge.capabilities.{name}]\nenvironments = ["{enabled}"]\n'
    fixture.write_plugin(
        "stripe-dotfiles",
        skills={name: {"SKILL.md": f"# {name}\n"} for name in ("writing", "jira-slack-to-jira")},
    )
    if environment == "mydata":
        extra += '[data.ai.plugin_bridge.capabilities.stripe-dotfiles.skills]\njira-slack-to-jira = "absent"\n'
    fixture.write_config(extra)
    text = fixture.config.read_text(encoding="utf-8")
    hosts = 'default_hosts = ["claude", "codex", "cursor"]\n'
    fixture.config.write_text(text.replace(hosts, f"{hosts}environment = {json.dumps(environment)}\n", 1))


def _marketplace_plugins(destination: Path, host_path: str) -> dict[str, dict]:
    manifest = destination / ".local/share/agent-plugins/marketplace" / host_path
    return {entry["name"]: entry for entry in json.loads(manifest.read_text())["plugins"]}


@pytest.mark.parametrize(
    ("environment", "selected", "absent"),
    [
        ("mydev", "mydev-capability", "mydata-capability"),
        ("mydata", "mydata-capability", "mydev-capability"),
    ],
)
def test_environment_fixture_selects_capability_and_cursor_projection(
    agent_source_fixture, environment, selected, absent
):
    """The selected environment gets its marketplace entry, Cursor copy, and mydata skill exclusions."""
    fixture = agent_source_fixture
    _environment_fixture(fixture, environment)
    managed = fixture.managed_files()
    local = ".cursor/plugins/local"
    assert f"{local}/{selected}/skills/example/SKILL.md" in managed
    assert not any(path.startswith(f"{local}/{absent}/") for path in managed)
    excluded = f"{local}/stripe-dotfiles/skills/jira-slack-to-jira/SKILL.md"
    assert (excluded in managed) is (environment == "mydev")
    assert f"{local}/stripe-dotfiles/skills/writing/SKILL.md" in managed

    first_apply = fixture.run("apply")
    assert first_apply.returncode == 0, first_apply.stderr
    expected_names = {"mkobit-dotfiles", "stripe-dotfiles", selected}
    for host_path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        assert set(_marketplace_plugins(fixture.destination, host_path)) == expected_names
    assert (fixture.destination / local / selected / "skills/example/SKILL.md").read_text() == f"# {selected}\n"
    assert not (fixture.destination / local / absent).exists()
    package = fixture.destination / ".local/share/agent-plugins/marketplace/plugins/stripe-dotfiles"
    for root in (
        package / "claude/skills",
        package / "codex/skills",
        fixture.destination / local / "stripe-dotfiles/skills",
    ):
        assert (root / "jira-slack-to-jira").exists() is (environment == "mydev")

    first_snapshot = _snapshot(fixture.destination)
    diff = fixture.run("--no-pager", "diff")
    assert diff.returncode == 0, diff.stderr
    assert diff.stdout == ""
    second_apply = fixture.run("apply")
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(fixture.destination) == first_snapshot


def test_marketplace_lists_inventory_plugins_for_selected_hosts(agent_source_fixture):
    """Marketplace entries and the bridge payload come from the inventory and its host selection."""
    fixture = agent_source_fixture
    skill = {"one": {"SKILL.md": "# One\n"}}
    fixture.write_plugin("everywhere", skills=skill)
    fixture.write_plugin("claude-only", skills=skill)
    fixture.write_plugin("disabled", skills=skill)
    fixture.write_config(
        '[data.ai.plugin_bridge.capabilities.claude-only]\nhosts = ["claude"]\n'
        '[data.ai.plugin_bridge.capabilities.disabled]\nenvironments = ["elsewhere"]\n'
    )
    result = fixture.run("apply")
    assert result.returncode == 0, result.stderr

    claude = _marketplace_plugins(fixture.destination, ".claude-plugin/marketplace.json")
    codex = _marketplace_plugins(fixture.destination, ".agents/plugins/marketplace.json")
    assert set(claude) == {"mkobit-dotfiles", "everywhere", "claude-only"}
    assert set(codex) == {"mkobit-dotfiles", "everywhere"}
    assert claude["claude-only"]["source"] == "./plugins/claude-only/claude"
    assert codex["everywhere"]["source"] == {"source": "local", "path": "./plugins/everywhere/codex"}

    bridge = fixture.run("execute-template", '{{ includeTemplate "ai/plugin-bridge" . }}')
    assert bridge.returncode == 0, bridge.stderr
    capabilities = json.loads(bridge.stdout)["capabilities"]
    assert "disabled" not in capabilities
    assert capabilities["claude-only"] == {
        "description": "claude-only fixture plugin.",
        "marketplace": "dotfiles",
        "hosts": ["claude"],
    }
    assert capabilities["everywhere"]["hosts"] == ["claude", "codex", "cursor"]
    provenance = SOURCE_ROOT / "dot_local/share/agent-plugins/marketplace/bridge-provenance.json.tmpl"
    rendered = fixture.run("execute-template", "--override-data", '{"ai": {"skills": {}}}', "-f", str(provenance))
    assert rendered.returncode == 0, rendered.stderr
    entries = {entry["name"]: entry for entry in json.loads(rendered.stdout)["capabilities"]}
    assert set(entries) == {"mkobit-dotfiles", "everywhere", "claude-only"}
    assert entries["everywhere"]["description"] == "everywhere fixture plugin."
    assert entries["everywhere"]["trust_class"] == "owned"

    fixture.write_config('[data.ai.plugin_bridge.capabilities.everywhere]\nexternal_source = "superpowers"\n')
    collision = fixture.run("execute-template", '{{ includeTemplate "ai/plugin-bridge" . }}')
    assert collision.returncode != 0
    assert "discovered plugin name equals an upstream or bundle capability" in collision.stderr


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
    assert payload["plugin_bridge"]["retired_plugins"]["superpowers"] == {
        "marketplace": "dotfiles",
        "hosts": ["claude", "codex"],
    }
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
def test_upstream_archive_preserves_files_and_prunes_old_skill_copies(tmp_path, ignore_layer):
    overlay_source = REPOSITORY_ROOT.parent.parent / "src/chezmoi"
    if ignore_layer == "overlay" and not (overlay_source / ".chezmoiignore.tmpl").is_file():
        pytest.skip("the overlay ignore policy is not available in this checkout")
    source, destination, config, contents = _upstream_fixture(
        tmp_path,
        "chezmoi_external",
        SOURCE_ROOT if ignore_layer == "base" else overlay_source,
    )
    package = destination / ".local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers"
    for stale in (package / "stale.txt", package / "nested/stale.txt"):
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n")
    sentinel = destination / ".local/share/agent-plugins/runtime/sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep\n")
    legacy_package = destination / ".local/share/agent-plugins/marketplace/plugins/superpowers"
    legacy_package.mkdir(parents=True)
    (legacy_package / "legacy.txt").write_text("remove\n")
    foreign_sibling = destination / ".local/share/agent-plugins/marketplace/plugins/custom-plugin"
    foreign_sibling.mkdir(parents=True)
    (foreign_sibling / "plugin.json").write_text('{"name":"custom-plugin"}\n')
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
    assert not legacy_package.exists()
    assert (foreign_sibling / "plugin.json").read_text() == '{"name":"custom-plugin"}\n'
    first_snapshot = _snapshot(destination)
    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(destination) == first_snapshot


@pytest.mark.parametrize("method", [None, "none"])
def test_upstream_plugin_disabled_after_install_removes_package(tmp_path, method):
    source, destination, config, _ = _upstream_fixture(tmp_path, "chezmoi_external")
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
