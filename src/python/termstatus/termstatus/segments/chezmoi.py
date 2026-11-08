import asyncio
from collections.abc import Sequence
from pathlib import Path

from whenever import TimeDelta

from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.segments.constants import (
    DIM,
    MAGENTA,
    RESET,
    get_icon,
)
from termstatus.segments.git import GitInfo, build_branch_url, fetch_git_info, format_right_parts, format_status_badge

_BASE_RELATIVE_PATH = Path("src/base")


def detect_chezmoi_root(cwd: Path) -> Path | None:
    current = cwd.resolve()
    while current != current.parent:
        if (current / ".chezmoiroot").exists():
            return current
        current = current.parent
    return None


_MAX_BRANCH_LEN = 24


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _format_repo(
    label: str,
    info: GitInfo,
    line: int,
    label_width: int = 0,
) -> Sequence[SegmentGenerationResult]:
    # label/body/right map to render.py's shared lead/body/right table columns —
    # cross-row alignment is that table's job now, not this function's. It aligns
    # column boundaries across rows, but the label and branch share one cell here,
    # so a ragged label (e.g. "overlay" vs "base") would still offset the branch
    # text within that cell; label_width pads the label so branches line up too.
    branch_url = build_branch_url(info.remote, info.branch) if bool(info.remote) else None
    branch_label = _truncate(info.branch, _MAX_BRANCH_LEN)
    branch_display = f"\033]8;;{branch_url}\033\\{branch_label}\033]8;;\033\\" if bool(branch_url) else branch_label

    label_prefix = f"{DIM}{label.ljust(label_width)}{RESET}  " if label else ""
    body_text = f"{label_prefix}{MAGENTA}{branch_display}{RESET}"
    badge_text = format_status_badge(info)

    right_filled = format_right_parts(info)

    results = [
        SegmentGenerationResult(
            line=line,
            index=0,
            column=0,
            segment=Segment(text=get_icon("branch")),
            generator="internal.chezmoi",
            cache_duration=TimeDelta(seconds=5),
        ),
        SegmentGenerationResult(
            line=line,
            index=0,
            column=1,
            segment=Segment(text=body_text),
            generator="internal.chezmoi",
            cache_duration=TimeDelta(seconds=5),
        ),
        SegmentGenerationResult(
            line=line,
            index=0,
            column=2,
            segment=Segment(text=badge_text),
            generator="internal.chezmoi",
            cache_duration=TimeDelta(seconds=5),
        ),
    ]

    if right_filled:
        results = [
            *results,
            SegmentGenerationResult(
                line=line,
                index=10,
                column=4,
                segment=Segment(text=" ".join(right_filled)),
                generator="internal.chezmoi",
                cache_duration=TimeDelta(seconds=5),
            ),
        ]

    return results


async def generate_chezmoi_segment(cwd: Path, chezmoi_root: Path) -> Sequence[SegmentGenerationResult]:
    base_path = chezmoi_root / _BASE_RELATIVE_PATH
    has_base = (base_path / ".git").exists()

    if has_base:
        overlay_info, base_info = await asyncio.gather(
            fetch_git_info(chezmoi_root, False),
            fetch_git_info(base_path, False),
        )
        if overlay_info is None and base_info is None:
            return []
        label_width = max(len("overlay"), len("base"))
        return [
            *(_format_repo("overlay", overlay_info, line=2, label_width=label_width) if overlay_info else []),
            *(_format_repo("base", base_info, line=3, label_width=label_width) if base_info else []),
        ]

    repo_info = await fetch_git_info(chezmoi_root, False)
    if repo_info is None:
        return []
    return [*_format_repo("", repo_info, line=2)]
