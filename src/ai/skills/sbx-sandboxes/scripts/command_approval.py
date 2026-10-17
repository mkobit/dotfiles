"""Approve single SBX commands from the packaged skill's tool list."""

from __future__ import annotations

import fnmatch
import json
import shlex
import sys
from contextlib import suppress
from pathlib import Path


def skill_patterns() -> list[str]:
    """Read the skill's bounded YAML list without a runtime YAML dependency."""
    lines = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return []
    patterns = []
    in_tools = False
    for line in lines[1:]:
        if line == "---":
            return patterns
        if line == "allowed-tools:":
            if in_tools or patterns:
                return []
            in_tools = True
        elif in_tools and line.startswith("  - Bash(sbx ") and line.endswith(")"):
            patterns.append(line.removeprefix("  - Bash(").removesuffix(")"))
        elif in_tools and line.strip():
            return []
    return []


def single_command(command: str) -> list[str]:
    """Exclude host shell expressions; quoted guest shell text stays data."""
    quote = ""
    escaped = False
    for character in command:
        if character == "\0":
            return []
        if escaped:
            if character in "\n\r":
                return []
            escaped = False
        elif quote == "'":
            if character == "'":
                quote = ""
        elif character == "\\":
            escaped = True
        elif quote == '"':
            if character == '"':
                quote = ""
            elif character in "$`":
                return []
        elif character in "'\"":
            quote = character
        elif character in ";&|<>(){}\n\r$`*?[]~#":
            return []
    if quote or escaped:
        return []
    return shlex.split(command)


def approved(payload: object, host: str) -> bool:
    """Check the native event shape and its literal SBX invocation."""
    if not isinstance(payload, dict):
        return False
    command = None
    if host == "codex":
        if payload.get("hook_event_name") != "PermissionRequest" or payload.get("tool_name") != "Bash":
            return False
        arguments = payload.get("tool_input")
        command = arguments.get("command") if isinstance(arguments, dict) else None
    elif host == "antigravity":
        tool = payload.get("toolCall")
        if not isinstance(tool, dict) or tool.get("name") != "run_command":
            return False
        arguments = tool.get("args")
        command = arguments.get("CommandLine") if isinstance(arguments, dict) else None
    if not isinstance(command, str):
        return False
    words = single_command(command)
    if not words or words[0] != "sbx":
        return False
    normalized = shlex.join(words)
    return any(
        fnmatch.fnmatchcase(normalized, pattern) and not (pattern.endswith(" --help") and "--" in words[:-1])
        for pattern in skill_patterns()
    )


def main() -> None:
    """Emit native approval or leave the host's normal policy in control."""
    host = sys.argv[1] if len(sys.argv) == 2 else ""
    allow = False
    with suppress(OSError, UnicodeError, ValueError):
        allow = approved(json.load(sys.stdin), host)
    if host == "antigravity":
        output = {"decision": "auto_approve" if allow else "allow"}
    elif allow:
        output = {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}
    else:
        output = {}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
