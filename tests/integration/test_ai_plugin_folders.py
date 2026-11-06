"""Check authored plugin folders and their native chezmoi lifecycle."""

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
PLUGINS = Path("dot_local/share/agent-plugins/marketplace/exact_plugins")
MARKETPLACE = Path(".local/share/agent-plugins/marketplace")
DEFAULT_HOSTS = ("claude", "codex", "cursor")


def _data(source: Path) -> dict:
    """Merge the TOML data files under source/.chezmoidata one level deep, like chezmoi."""
    merged: dict = {}
    for path in sorted((source / ".chezmoidata").rglob("*.toml")):
        stack = [(merged, tomllib.loads(path.read_text(encoding="utf-8")))]
        while stack:
            target, values = stack.pop()
            for key, value in values.items():
                if isinstance(value, dict):
                    stack.append((target.setdefault(key, {}), value))
                else:
                    target[key] = value
    return merged


def plugin_shape_errors(source: Path, hosts: dict[str, list[str]]) -> list[str]:
    """Return shape errors for every plugin folder under source.

    Each selected host needs its manifest in the host package, which is the plugin
    folder or the host_dirs subfolder. Each package needs a skills/ folder or other
    content, and each skill needs SKILL.md or SKILL.md.tmpl.
    """
    errors = []
    data = _data(source)
    for folder in sorted((source / PLUGINS).glob("exact_*")):
        name = folder.name.removeprefix("exact_")
        identity = data.get("ai", {}).get("plugins", {}).get(name)
        if not identity or not identity.get("description"):
            errors.append(f"{name}: missing ai.plugins.{name}.description")
            continue
        host_dirs = identity.get("host_dirs", {})
        for host in hosts.get(name, DEFAULT_HOSTS):
            package = folder / f"exact_{host_dirs[host]}" if host in host_dirs else folder
            if not (package / f"exact_dot_{host}-plugin/plugin.json.tmpl").is_file():
                errors.append(f"{name}: missing {host} manifest in {package.relative_to(folder)}")
            content = [path for path in package.iterdir() if not re.fullmatch(r"exact_dot_[a-z]+-plugin", path.name)]
            if not content:
                errors.append(f"{name}: {host} package has no skills/ folder or other content")
            errors.extend(
                f"{name}: {skill.name} has no SKILL.md"
                for skill in sorted((package / "exact_skills").glob("exact_*"))
                if not any((skill / f).is_file() for f in ("SKILL.md", "SKILL.md.tmpl"))
            )
    return errors


def test_every_base_plugin_folder_has_the_shape_of_its_hosts():
    bridge = _data(SOURCE_ROOT)["ai"]["plugin_bridge"]["capabilities"]
    hosts = {name: value["hosts"] for name, value in bridge.items() if "hosts" in value}
    assert (SOURCE_ROOT / PLUGINS / "exact_mkobit-dotfiles").is_dir()
    assert plugin_shape_errors(SOURCE_ROOT, hosts) == []


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build a source with one shared-folder plugin and one host-subfolder plugin."""
    source, destination = tmp_path / "source", tmp_path / "destination"
    destination.mkdir()
    for relative in (
        ".chezmoiignore.tmpl",
        ".chezmoidata/ai/plugin-bridge.toml",
        ".chezmoiscripts/run_onchange_before_00-agent-plugin-deselect.sh.tmpl",
        "dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl",
        "dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl",
        "dot_local/share/agent-plugins/marketplace/dot_cursor-plugin/marketplace.json.tmpl",
    ):
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, source / relative)
    shutil.copytree(SOURCE_ROOT / ".chezmoitemplates/ai", source / ".chezmoitemplates/ai")

    def write(relative: str, text: str) -> None:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    alpha = PLUGINS / "exact_alpha"
    for host in DEFAULT_HOSTS:
        write(
            f"{alpha}/exact_dot_{host}-plugin/plugin.json.tmpl",
            f'{{{{ includeTemplate "ai/{host}/plugin-manifest" (dict "name" "alpha" "root" .) -}}}}\n',
        )
    write(f"{alpha}/exact_skills/exact_one/SKILL.md", "# One\n")
    write(f"{alpha}/exact_skills/exact_two/SKILL.md.tmpl", "# {{ .fixture.title }}\n")
    write(".chezmoidata/ai/plugins/alpha.toml", '[ai.plugins.alpha]\ndescription = "Shared folder."\n')

    beta = PLUGINS / "exact_beta"
    for host in ("claude", "codex"):
        write(
            f"{beta}/exact_{host}/exact_dot_{host}-plugin/plugin.json.tmpl",
            f'{{{{ includeTemplate "ai/{host}/plugin-manifest" (dict "name" "beta" "root" . '
            f'"extra" (dict "mcpServers" "./.mcp.json")) -}}}}\n',
        )
        write(f"{beta}/exact_{host}/dot_mcp.json", json.dumps({"mcpServers": {host: {}}}) + "\n")
    write(
        ".chezmoidata/ai/plugins/beta.toml",
        '[ai.plugins.beta]\ndescription = "Host folders."\nauthor = "fixture"\n'
        '[ai.plugins.beta.host_dirs]\nclaude = "claude"\ncodex = "codex"\n',
    )
    config = tmp_path / "chezmoi.toml"
    return source, destination, config


def _config(config: Path, beta: str = "", extra: str = "") -> None:
    config.write_text(
        '[data.fixture]\ntitle = "Two"\n'
        '[data.mise.global_tools.bun]\ninstallation_method = "none"\n'
        '[data.ai.plugin_bridge.capabilities.beta]\nhosts = ["claude", "codex"]\n' + beta + extra,
        encoding="utf-8",
    )


def _chezmoi(source: Path, destination: Path, config: Path, *args: str) -> str:
    result = subprocess.run(
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
            "--no-tty",
            *args,
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sources(destination: Path, manifest: str) -> dict[str, object]:
    return {entry["name"]: entry["source"] for entry in _json(destination / MARKETPLACE / manifest)["plugins"]}


def test_plugin_folders_converge_through_native_apply(tmp_path):
    source, destination, config = _fixture(tmp_path)
    _config(config)
    assert plugin_shape_errors(source, {"beta": ["claude", "codex"]}) == []
    plugins = destination / MARKETPLACE / "plugins"

    _chezmoi(source, destination, config, "apply")
    alpha = _json(plugins / "alpha/.claude-plugin/plugin.json")
    assert alpha["skills"] == "./skills"
    assert alpha["author"] == {
        "name": _chezmoi(source, destination, config, "execute-template", "{{ .chezmoi.username }}")
    }
    assert (plugins / "alpha/skills/two/SKILL.md").read_text() == "# Two\n"
    assert _json(plugins / "alpha/.codex-plugin/plugin.json")["interface"]["capabilities"] == ["one", "two"]
    beta = _json(plugins / "beta/claude/.claude-plugin/plugin.json")
    assert beta["mcpServers"] == "./.mcp.json"
    assert "skills" not in beta
    assert not (plugins / "beta/.cursor-plugin/plugin.json").exists()
    assert _sources(destination, ".claude-plugin/marketplace.json") == {
        "alpha": "./plugins/alpha",
        "beta": "./plugins/beta/claude",
    }
    assert _sources(destination, ".agents/plugins/marketplace.json")["beta"]["path"] == "./plugins/beta/codex"
    assert _sources(destination, ".cursor-plugin/marketplace.json") == {"alpha": "./plugins/alpha"}
    assert _chezmoi(source, destination, config, "diff") == ""

    version = alpha["version"]
    (source / PLUGINS / "exact_alpha/exact_skills/exact_one/SKILL.md").write_text("# One, edited\n")
    _chezmoi(source, destination, config, "apply")
    assert (plugins / "alpha/skills/one/SKILL.md").read_text() == "# One, edited\n"
    assert _json(plugins / "alpha/.claude-plugin/plugin.json")["version"] != version

    _config(
        config,
        extra='[data.ai.plugin_bridge.capabilities.alpha]\nhosts = ["claude", "codex"]\n'
        '[data.ai.plugin_bridge.capabilities.alpha.skills]\none = "absent"\n',
    )
    _chezmoi(source, destination, config, "apply")
    assert not (plugins / "alpha/skills/one").exists()
    assert not (plugins / "alpha/.cursor-plugin/plugin.json").exists()
    assert _json(plugins / "alpha/.codex-plugin/plugin.json")["interface"]["capabilities"] == ["two"]
    assert _sources(destination, ".cursor-plugin/marketplace.json") == {}

    # Selecting the skill again restores it without a prompt; disabling beta removes its folder.
    _config(config, beta="enabled = false\n")
    _chezmoi(source, destination, config, "apply")
    assert (plugins / "alpha/skills/one/SKILL.md").read_text() == "# One, edited\n"
    assert not (plugins / "beta").exists()
    assert set(_sources(destination, ".claude-plugin/marketplace.json")) == {"alpha"}

    shutil.rmtree(source / PLUGINS / "exact_alpha")
    _chezmoi(source, destination, config, "apply")
    assert not (plugins / "alpha").exists()
    assert _sources(destination, ".claude-plugin/marketplace.json") == {}
    assert _chezmoi(source, destination, config, "diff") == ""
