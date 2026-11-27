"""Read update policy from assembled chezmoi data."""

import json
import subprocess
from collections.abc import Mapping
from os import devnull
from pathlib import Path
from typing import Any

from bin_updater.cooldown import parse_cooldown_to_seconds
from chezmoi_cli import ChezmoiCli

DEFAULT_SOURCE = Path("src/chezmoi")


def load_policy(source: Path = DEFAULT_SOURCE) -> Mapping[str, Any]:
    """Read the update policy for the selected source without initializing it."""
    try:
        result = ChezmoiCli(source=source, config=devnull, config_format="toml").data(format="json").run(check=True)
        policy = json.loads(result.stdout)["bin_updates"]
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Could not read binary update policy from chezmoi source {source}") from error
    if not isinstance(policy, dict):
        raise ValueError("Expected a bin_updates table in chezmoi data")
    return policy


def configured_age(policy: Mapping[str, Any], tool: str, *, mise: bool = False) -> str | int:
    key = "mise_minimum_release_age" if mise else "minimum_release_age"
    age = policy.get("tools", {}).get(tool, policy[key])
    parse_cooldown_to_seconds(age)
    return age
