"""Per-tool CLI adaptation for sandboxed runs.

Autonomous (no-human-in-the-loop) runs bypass each tool's own permission
prompts by default; the outer sandbox is the security boundary instead.
Passing skip_permissions=False keeps a tool's own prompts active — e.g. to
still get asked before `git push`/`gh pr create`/`gh pr merge` per the
existing command-policy catalog — while staying sandboxed underneath.
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
    skip_permissions: bool = True,
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
            *([] if not skip_permissions or _SKIP_PERMS in command else [_SKIP_PERMS]),
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
            *([] if not skip_permissions or _SKIP_PERMS in command else [_SKIP_PERMS]),
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
