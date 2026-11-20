"""Check selected authored skill display names from rendered chezmoi data."""

import argparse
import json
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path("dot_local/share/agent-plugins/marketplace/exact_plugins")


def display_name_error(path: Path) -> str | None:
    """Return an error unless the metadata contains a quoted, nonempty name."""
    metadata = path / "exact_agents/openai.yaml"
    try:
        node = yaml.compose(metadata.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        return f"{metadata}: cannot read interface.display_name: {error}"
    if isinstance(node, yaml.MappingNode):
        interface = next((v for k, v in node.value if k.value == "interface"), None)
        if isinstance(interface, yaml.MappingNode):
            name = next((v for k, v in interface.value if k.value == "display_name"), None)
            if (
                isinstance(name, yaml.ScalarNode)
                and name.tag == "tag:yaml.org,2002:str"
                and name.style in ("'", '"')
                and name.value.strip()
            ):
                return None
    return f"{metadata}: interface.display_name must be a quoted, nonempty string"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--host", required=True)
    parser.add_argument("--config", required=True, help="JSON from chezmoi data --format json, or - for stdin")
    args = parser.parse_args()
    try:
        config = json.load(sys.stdin) if args.config == "-" else json.loads(Path(args.config).read_text())
        ai = config.get("ai", {})
        bridge = ai.get("plugin_bridge", {})
        plugins = ai.get("plugins", {})
        plugin_root = args.source_root / PLUGIN_ROOT
        if not plugin_root.is_dir():
            raise ValueError(f"{plugin_root}: authored plugin directory missing")
        errors = []
        for plugin in sorted(plugin_root.glob("exact_*")):
            if not plugin.is_dir():
                continue
            name = plugin.name.removeprefix("exact_")
            decision = bridge.get("capabilities", {}).get(name, {})
            environments = decision.get("environments")
            if not decision.get("enabled", True) or (
                environments is not None and bridge.get("environment", "default") not in environments
            ):
                continue
            if args.host not in decision.get("hosts", bridge.get("default_hosts", ["claude", "codex", "cursor"])):
                continue
            host_dir = plugins.get(name, {}).get("host_dirs", {}).get(args.host)
            package = plugin / f"exact_{host_dir}" if host_dir else plugin
            for skill in sorted((package / "exact_skills").glob("exact_*")):
                if not skill.is_dir():
                    continue
                skill_name = skill.name.removeprefix("exact_")
                if decision.get("skills", {}).get(skill_name, "present") == "absent":
                    continue
                error = display_name_error(skill)
                if error is not None:
                    errors.append(f"{name}/{skill_name}: {error}")
                else:
                    print(f"{name}/{skill_name}: {skill}")
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
    except (ValueError, OSError, TypeError, AttributeError) as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
