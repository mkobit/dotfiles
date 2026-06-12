from pathlib import Path

from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payloads.antigravity import AntigravityPayload
from termstatus.segments.constants import BLUE, CYAN, DIM, GREEN, MAGENTA, RESET, WHITE, YELLOW

AGENT_STATE_COLORS = {
    "idle": DIM,
    "thinking": CYAN,
    "working": BLUE,
    "tool_use": MAGENTA,
    "initializing": YELLOW,
}


def format_agent_state(payload: AntigravityPayload) -> list[SegmentGenerationResult]:
    state = payload.agent_state
    if not state:
        return []

    color = AGENT_STATE_COLORS.get(state, WHITE)
    return [
        SegmentGenerationResult(
            line=3,
            index=10,
            generator="internal.antigravity.agent_state",
            segment=Segment(text=f"{color}[{state}]{RESET}"),
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
            segment=Segment(text=f"{GREEN}{payload.model.display_name}{RESET}"),
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
            segment=Segment(text=f"{BLUE}{basename}{RESET}"),
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
            segment=Segment(text=f"{YELLOW}{branch}{dirty_marker}{RESET}"),
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
            segment=Segment(text=f"{CYAN}{percent:.1f}% context{RESET}"),
        )
    ]


def generate_title(payload: AntigravityPayload) -> str:
    basename = Path(payload.cwd).name if payload.cwd else None
    display_name = payload.model.display_name if payload.model else None
    short_id = payload.conversation_id.split("-")[0] if payload.conversation_id else None
    candidates = [
        f"[{payload.agent_state}]" if payload.agent_state else None,
        basename,
        f"({display_name})" if display_name else None,
        f"- {short_id}" if short_id else None,
    ]
    parts = [part for part in candidates if part]
    return " ".join(parts) if parts else "Antigravity"
