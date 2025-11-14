import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

# For a definitive list of valid hook events, see the official documentation:
# https://code.claude.com/docs/en/hooks-guide
VALID_HOOK_EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Notification",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
]

@dataclass(frozen=True)
class Hook:
    hook_type: str
    command: str

@dataclass(frozen=True)
class Matcher:
    matcher: str
    hooks: List[Hook]

@dataclass(frozen=True)
class HookConfig:
    hooks: Dict[str, List[Matcher]]

def to_dict_factory(data: Any) -> Dict[str, Any]:
    """
    Custom dict factory to handle renaming 'hook_type' to 'type' for JSON output.
    """
    result = asdict(data)
    for matchers in result.get("hooks", {}).values():
        for matcher in matchers:
            for hook in matcher.get("hooks", []):
                if "hook_type" in hook:
                    hook["type"] = hook.pop("hook_type")
    return result

def generate_hook_config(event: str, matcher_str: str, command: str) -> Dict[str, Any]:
    """
    Generates the hook configuration dictionary from the provided arguments.
    """
    hook = Hook(hook_type="command", command=command)
    matcher = Matcher(matcher=matcher_str, hooks=[hook])
    config = HookConfig(hooks={event: [matcher]})
    return to_dict_factory(config)
