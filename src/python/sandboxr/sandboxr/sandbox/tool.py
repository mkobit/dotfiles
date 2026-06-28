"""Per-tool CLI adaptation for autonomous (no-human-in-the-loop) runs.

The outer sandbox is the security boundary; each tool's own permission
prompts are bypassed because they would only add friction here.
"""

from collections.abc import Mapping
from pathlib import Path

_DEFAULT_CLAUDE_SETTINGS = (
    Path.home() / ".config" / "ai-policy" / "claude" / "autonomous-settings.json"
)
_DEFAULT_AGY_SETTINGS = Path.home() / ".config" / "ai-policy" / "agy" / "autonomous-settings.json"
_DEFAULT_OPENCODE_CONFIG = Path.home() / ".config" / "ai-policy" / "opencode" / "autonomous.json"

_SKIP_PERMS = "--dangerously-skip-permissions"


def adapt_command(
    command: list[str],
    base_env: Mapping[str, str],
    *,
    claude_settings: Path | None = None,
    agy_settings: Path | None = None,
    opencode_config: Path | None = None,
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
            *([] if _SKIP_PERMS in command else [_SKIP_PERMS]),
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
            *([] if _SKIP_PERMS in command else [_SKIP_PERMS]),
            # Do NOT pass --sandbox: combining with --dangerously-skip-permissions
            # auto-approves bypassing the sandbox itself (antigravity-cli #36).
        ]
        return adapted, {}
    oc_path = opencode_config or _DEFAULT_OPENCODE_CONFIG
    if tool == "opencode":
        # Deliberately do NOT set OPENCODE_HARDENED_MODE=1: that engages
        # opencode's own bwrap inside our bwrap, creating nested namespaces.
        return list(command), {"OPENCODE_CONFIG": str(oc_path)}
    return list(command), {}
