"""Per-tool CLI adaptation for sandboxed runs.

Injects ai-policy settings files when they exist.
Callers must explicitly supply permission-bypass flags (such as
`--dangerously-skip-permissions`) if desired.
"""

from collections.abc import Mapping
from pathlib import Path

_DEFAULT_CLAUDE_SETTINGS = (
    Path.home() / ".config" / "ai-policy" / "claude" / "autonomous-settings.json"
)
_DEFAULT_AGY_SETTINGS = Path.home() / ".config" / "ai-policy" / "agy" / "autonomous-settings.json"


def adapt_command(
    command: list[str],
    base_env: Mapping[str, str],
    *,
    claude_settings: Path | None = None,
    agy_settings: Path | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Return (adapted_command, extra_env) for the given tool.

    Callers merge extra_env into SandboxSpec.extra_env.
    Paths default to the ai-policy config locations.
    """
    tool = Path(command[0]).name
    settings_path = claude_settings or _DEFAULT_CLAUDE_SETTINGS
    if tool == "claude":
        adapted = [
            *command,
            *(
                ["--settings", str(settings_path)]
                if "--settings" not in command and settings_path.exists()
                else []
            ),
        ]
        return adapted, {}
    agy_path = agy_settings or _DEFAULT_AGY_SETTINGS
    if tool == "agy":
        adapted = [
            *command,
            *(
                ["--settings", str(agy_path)]
                if "--settings" not in command and agy_path.exists()
                else []
            ),
        ]
        return adapted, {}
    return list(command), {}
