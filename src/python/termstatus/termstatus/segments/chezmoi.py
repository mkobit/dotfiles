import asyncio
from collections.abc import Sequence
from pathlib import Path

from whenever import TimeDelta

from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.segments.constants import (
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_icon,
)
from termstatus.segments.git import (
    GitInfo,
    _check_is_repo,
    _get_ahead_behind,
    _get_branch_and_remote,
    _get_stash_count,
    _get_status,
)

_BASE_RELATIVE_PATH = Path("src/base")


def detect_chezmoi_root(cwd: Path) -> Path | None:
    current = cwd.resolve()
    while current != current.parent:
        if (current / ".chezmoiroot").exists():
            base_git = current / _BASE_RELATIVE_PATH / ".git"
            if base_git.exists():
                return current
        current = current.parent
    return None


async def _fetch_repo_info(repo_path: Path) -> GitInfo | None:
    if not await _check_is_repo(repo_path):
        return None

    branch_info, status_info, ahead_behind_info, stash_count = await asyncio.gather(
        _get_branch_and_remote(repo_path),
        _get_status(repo_path),
        _get_ahead_behind(repo_path),
        _get_stash_count(repo_path),
    )

    return GitInfo(
        branch=branch_info.branch,
        remote=branch_info.remote,
        dirty=status_info.dirty,
        staged=status_info.staged,
        untracked=status_info.untracked,
        ahead=ahead_behind_info.ahead,
        behind=ahead_behind_info.behind,
        is_repo=True,
        stash_count=stash_count,
    )


def _build_branch_url(remote: str, branch: str) -> str:
    if branch == "HEAD":
        return remote
    if "gitlab.com" in remote:
        return f"{remote}/-/tree/{branch}"
    return f"{remote}/tree/{branch}"


def _format_repo(
    label: str,
    info: GitInfo,
    line: int,
) -> Sequence[SegmentGenerationResult]:
    branch_url = _build_branch_url(info.remote, info.branch) if info.remote else None
    branch_display = f"\033]8;;{branch_url}\033\\{info.branch}\033]8;;\033\\" if branch_url else info.branch

    status_parts = [
        f"{RED}{get_icon('dirty')}{RESET}" if info.dirty else None,
        f"{YELLOW}{get_icon('staged')}{RESET}" if info.staged else None,
        f"{CYAN}{get_icon('untracked')}{RESET}" if info.untracked else None,
    ]
    filled = [s for s in status_parts if s is not None]
    if not filled:
        filled = [f"{GREEN}{get_icon('clean')}{RESET}"]

    left_text = f"{DIM}{label}{RESET} {MAGENTA}{get_icon('branch')} {branch_display}{RESET} [{''.join(filled)}]"

    right_parts = [
        f"{GREEN}↑{info.ahead}{RESET}" if info.ahead > 0 else None,
        f"{RED}↓{info.behind}{RESET}" if info.behind > 0 else None,
        f"{YELLOW}{get_icon('stash')}{info.stash_count}{RESET}" if info.stash_count > 0 else None,
    ]
    right_filled = [p for p in right_parts if p is not None]

    remote_text = None
    if info.remote:
        platform_icon = (
            get_icon("github")
            if "github.com" in info.remote
            else get_icon("gitlab")
            if "gitlab.com" in info.remote
            else get_icon("remote")
        )
        remote_text = f"\033]8;;{info.remote}\033\\{platform_icon}\033]8;;\033\\"

    if remote_text:
        right_filled = [*right_filled, remote_text]

    results = [
        SegmentGenerationResult(
            line=line,
            index=0,
            column=0,
            segment=Segment(text=left_text),
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
                column=3,
                segment=Segment(text=" ".join(right_filled)),
                generator="internal.chezmoi",
                cache_duration=TimeDelta(seconds=5),
            ),
        ]

    return results


def _chezmoi_dir_indicator() -> SegmentGenerationResult:
    return SegmentGenerationResult(
        line=1,
        index=0,
        column=0,
        segment=Segment(text=f"{MAGENTA}{get_icon('chezmoi')} chezmoi{RESET}"),
        generator="internal.chezmoi",
        cache_duration=TimeDelta(seconds=5),
    )


async def generate_chezmoi_segment(cwd: Path, chezmoi_root: Path) -> Sequence[SegmentGenerationResult]:
    overlay_path = chezmoi_root
    base_path = chezmoi_root / _BASE_RELATIVE_PATH

    overlay_info, base_info = await asyncio.gather(
        _fetch_repo_info(overlay_path),
        _fetch_repo_info(base_path),
    )

    if overlay_info is None and base_info is None:
        return []

    return [
        _chezmoi_dir_indicator(),
        *(_format_repo("overlay", overlay_info, line=2) if overlay_info else []),
        *(_format_repo("base", base_info, line=3) if base_info else []),
    ]
