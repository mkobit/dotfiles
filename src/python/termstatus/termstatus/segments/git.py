from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from whenever import TimeDelta

from termstatus.git_status import probe_git
from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.segments.constants import (
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_icon,
)

# Wider than agy's probe budget: slow git wrappers can exceed 100 ms per call.
_GIT_TIMEOUT: Final[TimeDelta] = TimeDelta(milliseconds=300)


@dataclass
class GitInfo:
    branch: str
    remote: str | None = None
    dirty: bool = False
    staged: bool = False
    untracked: bool = False
    ahead: int = 0
    behind: int = 0
    is_repo: bool = True
    is_worktree: bool = False
    stash_count: int = 0


def _normalize_remote(url: str | None) -> str | None:
    if url is None:
        return None
    if url.startswith("git@"):
        url = url.replace(":", "/").replace("git@", "https://")
    return url.removesuffix(".git")


def build_branch_url(remote: str, branch: str) -> str:
    if branch == "HEAD":
        return remote
    if "gitlab.com" in remote:
        return f"{remote}/-/tree/{branch}"
    return f"{remote}/tree/{branch}"


async def fetch_git_info(cwd: Path, is_worktree: bool) -> GitInfo | None:
    vcs = await probe_git(str(cwd), _GIT_TIMEOUT)
    if vcs is None:
        return None
    return GitInfo(
        branch=vcs.branch or "HEAD",
        remote=_normalize_remote(vcs.origin_url),
        dirty=vcs.dirty,
        staged=vcs.staged,
        untracked=vcs.untracked,
        ahead=vcs.ahead,
        behind=vcs.behind,
        is_repo=vcs.is_repo,
        is_worktree=is_worktree,
        stash_count=vcs.stash_count,
    )


async def generate_git_segment(cwd: Path, is_worktree: bool) -> Sequence[SegmentGenerationResult]:
    return format_git_full(await fetch_git_info(cwd, is_worktree))


def format_status_badge(info: GitInfo) -> str:
    status_parts = [
        f"{RED}{get_icon('dirty')}{RESET}" if info.dirty else None,
        f"{YELLOW}{get_icon('staged')}{RESET}" if info.staged else None,
        f"{CYAN}{get_icon('untracked')}{RESET}" if info.untracked else None,
    ]
    filled = [s for s in status_parts if s is not None]
    if not filled:
        filled = [f"{GREEN}{get_icon('clean')}{RESET}"]
    return f"[{''.join(filled)}]"


def format_right_parts(info: GitInfo) -> list[str]:
    right_parts = [
        f"{GREEN}↑{info.ahead}{RESET}" if info.ahead > 0 else None,
        f"{RED}↓{info.behind}{RESET}" if info.behind > 0 else None,
        f"{YELLOW}{get_icon('stash')}{info.stash_count}{RESET}" if info.stash_count > 0 else None,
    ]
    right_filled = [p for p in right_parts if p is not None]

    if bool(info.remote):
        platform_icon = (
            get_icon("github")
            if "github.com" in info.remote
            else get_icon("gitlab")
            if "gitlab.com" in info.remote
            else get_icon("remote")
        )
        right_filled = [*right_filled, f"\033]8;;{info.remote}\033\\{platform_icon}\033]8;;\033\\"]
    return right_filled


def format_git_full(info: GitInfo | None) -> list[SegmentGenerationResult]:
    if not info:
        return []

    branch_icon = get_icon("worktree") if info.is_worktree else get_icon("branch")
    branch_url = build_branch_url(info.remote, info.branch) if bool(info.remote) else None
    branch_display = f"\033]8;;{branch_url}\033\\{info.branch}\033]8;;\033\\" if bool(branch_url) else info.branch

    branch_text = f"{MAGENTA}{branch_icon} {branch_display}{RESET} {format_status_badge(info)}"

    results = [
        SegmentGenerationResult(
            line=1,
            index=10,
            column=1,
            segment=Segment(text=branch_text),
            generator="internal.git",
            cache_duration=TimeDelta(seconds=5),
        )
    ]

    right_filled = format_right_parts(info)

    if right_filled:
        results = [
            *results,
            SegmentGenerationResult(
                line=1,
                index=30,
                column=3,
                segment=Segment(text=" ".join(right_filled)),
                generator="internal.git",
                cache_duration=TimeDelta(seconds=5),
            ),
        ]

    return results
