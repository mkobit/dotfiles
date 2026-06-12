from pathlib import Path

from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payloads.antigravity import AntigravityPayload


def format_agent_state(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    state = payload.agent_state
    if not state:
        return []

    color = "white"
    if state == "idle":
        color = "grey62"
    elif state == "thinking":
        color = "cyan"
    elif state == "working":
        color = "blue"
    elif state == "tool_use":
        color = "magenta"
    elif state == "initializing":
        color = "yellow"

    return [
        SegmentGenerationResult(
            line=3,
            index=10,
            generator="internal.antigravity.agent_state",
            segment=Segment(text=f"[{color}][{state}][/{color}]"),
        )
    ]


def format_model_info(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    if not payload.model or not payload.model.display_name:
        return []

    return [
        SegmentGenerationResult(
            line=3,
            index=20,
            generator="internal.antigravity.model_info",
            segment=Segment(text=f"[green]{payload.model.display_name}[/green]"),
        )
    ]


def format_workspace_info(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    cwd = payload.cwd
    if not cwd:
        return []

    basename = Path(cwd).name
    return [
        SegmentGenerationResult(
            line=3,
            index=30,
            generator="internal.antigravity.workspace",
            segment=Segment(text=f"[blue]{basename}[/blue]"),
        )
    ]


def format_vcs_info(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    if not payload.vcs or not payload.vcs.branch:
        return []

    branch = payload.vcs.branch
    dirty_marker = "*" if payload.vcs.dirty else ""
    return [
        SegmentGenerationResult(
            line=3,
            index=40,
            generator="internal.antigravity.vcs",
            segment=Segment(text=f"[yellow]{branch}{dirty_marker}[/yellow]"),
        )
    ]


def format_context_usage(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    if not payload.context_window or payload.context_window.used_percentage is None:
        return []

    percent = payload.context_window.used_percentage
    return [
        SegmentGenerationResult(
            line=3,
            index=50,
            generator="internal.antigravity.context_usage",
            segment=Segment(text=f"[cyan]{percent:.1f}% context[/cyan]"),
        )
    ]


def generate_title(payload: AntigravityPayload) -> str:
    parts = []

    # State
    if payload.agent_state:
        parts.append(f"[{payload.agent_state}]")

    # Workspace
    if payload.cwd:
        basename = Path(payload.cwd).name
        parts.append(basename)

    # Model
    if payload.model and payload.model.display_name:
        parts.append(f"({payload.model.display_name})")

    # Session
    if payload.conversation_id:
        short_id = payload.conversation_id.split("-")[0]
        parts.append(f"- {short_id}")

    return " ".join(parts) if parts else "Antigravity"
