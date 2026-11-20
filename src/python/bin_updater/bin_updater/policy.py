"""Read release age policy from chezmoi data."""

import tomllib
from pathlib import Path

from bin_updater.cooldown import parse_cooldown_to_seconds


def configured_age(path: Path, tool: str, *, mise: bool = False) -> str | int | None:
    if not path.exists():
        return None
    policy = tomllib.loads(path.read_text(encoding="utf-8"))["bin_updates"]
    key = "mise_minimum_release_age" if mise else "minimum_release_age"
    age = policy.get("tools", {}).get(tool, policy[key])
    parse_cooldown_to_seconds(age)
    return age
