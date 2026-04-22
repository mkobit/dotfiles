import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

from whenever import TimeDelta

from claude_statusline.models import GitInfo, Segment, SegmentGenerationResult
from claude_statusline.segments.constants import (
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_icon,
)

logger = logging.getLogger(__name__)


class BranchRemoteInfo(NamedTuple):
    branch: str
    remote: str | None


class GitStatusInfo(NamedTuple):
    dirty: bool
    staged: bool
    untracked: bool


class AheadBehindInfo(NamedTuple):
    ahead: int
    behind: int


async def _run_git_cmd(cmd: list[str], cwd: Path) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)
        if proc.returncode == 0:
            return stdout.decode().strip()
    except (TimeoutError, Exception) as e:
        logger.debug(f"Git command failed: {e}")
    return None


async def _check_is_repo(cwd: Path) -> bool:
    res = await _run_git_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    return res == "true"


async def _get_branch_and_remote(cwd: Path) -> BranchRemoteInfo:
    branch = "HEAD"
    remote = None

    branch_res = await _run_git_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if branch_res:
        branch = branch_res

    remote_res = await _run_git_cmd(["git", "ls-remote", "--get-url", "origin"], cwd)
    if remote_res:
        remote_url = remote_res
        if remote_url.startswith("git@"):
            remote_url = remote_url.replace(":", "/").replace("git@", "https://")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        remote = remote_url

    return BranchRemoteInfo(branch=branch, remote=remote)


async def _get_status(cwd: Path) -> GitStatusInfo:
    dirty = False
    staged = False
    untracked = False

    res = await _run_git_cmd(["git", "status", "--porcelain"], cwd)
    if res:
        lines = res.splitlines()
        staged = any(line[0] not in (" ", "?") for line in lines)
        dirty = any(line[1] != " " and not line.startswith("??") for line in lines)
        untracked = any(line.startswith("??") for line in lines)

    return GitStatusInfo(dirty=dirty, staged=staged, untracked=untracked)


async def _get_ahead_behind(cwd: Path) -> AheadBehindInfo:
    ahead = 0
    behind = 0

    res = await _run_git_cmd(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd)
    if res:
        try:
            a, b = map(int, res.split())
            ahead = a
            behind = b
        except ValueError:
            pass

    return AheadBehindInfo(ahead=ahead, behind=behind)


async def _get_stash_count(cwd: Path) -> int:
    res = await _run_git_cmd(["git", "stash", "list"], cwd)
    return len(res.splitlines()) if res else 0


def _build_branch_url(remote: str, branch: str) -> str:
    if branch == "HEAD":
        return remote
    if "gitlab.com" in remote:
        return f"{remote}/-/tree/{branch}"
    return f"{remote}/tree/{branch}"


async def generate_git_segment(cwd: Path, is_worktree: bool) -> Sequence[SegmentGenerationResult]:
    if not await _check_is_repo(cwd):
        return []

    branch_task = asyncio.create_task(_get_branch_and_remote(cwd))
    status_task = asyncio.create_task(_get_status(cwd))
    ahead_behind_task = asyncio.create_task(_get_ahead_behind(cwd))
    stash_task = asyncio.create_task(_get_stash_count(cwd))

    branch_info, status_info, ahead_behind_info, stash_count = await asyncio.gather(
        branch_task, status_task, ahead_behind_task, stash_task
    )

    info = GitInfo(
        branch=branch_info.branch,
        remote=branch_info.remote,
        dirty=status_info.dirty,
        staged=status_info.staged,
        untracked=status_info.untracked,
        ahead=ahead_behind_info.ahead,
        behind=ahead_behind_info.behind,
        is_repo=True,
        is_worktree=is_worktree,
        stash_count=stash_count,
    )

    result = format_git_full(info)
    if result:
        return [result]
    return []


def format_git_full(info: GitInfo | None) -> SegmentGenerationResult | None:
    if not info:
        return None

    branch_icon = get_icon("worktree") if info.is_worktree else get_icon("branch")
    branch_url = _build_branch_url(info.remote, info.branch) if info.remote else None
    branch_display = f"\033]8;;{branch_url}\033\\{info.branch}\033]8;;\033\\" if branch_url else info.branch
    parts = [f"{MAGENTA}{branch_icon} {branch_display}{RESET}"]

    status_parts = [
        f"{RED}{get_icon('dirty')}{RESET}" if info.dirty else None,
        f"{YELLOW}{get_icon('staged')}{RESET}" if info.staged else None,
        f"{CYAN}{get_icon('untracked')}{RESET}" if info.untracked else None,
    ]
    filled = [s for s in status_parts if s]
    if not filled:
        filled = [f"{GREEN}{get_icon('clean')}{RESET}"]

    parts.append(f"[{''.join(filled)}]")

    if info.ahead > 0:
        parts.append(f"{GREEN}↑{info.ahead}{RESET}")
    if info.behind > 0:
        parts.append(f"{RED}↓{info.behind}{RESET}")
    if info.stash_count > 0:
        parts.append(f"{YELLOW}{get_icon('stash')}{info.stash_count}{RESET}")

    if info.remote:
        platform_icon = (
            get_icon("github")
            if "github.com" in info.remote
            else get_icon("gitlab")
            if "gitlab.com" in info.remote
            else get_icon("remote")
        )
        parts.append(f"[ \033]8;;{info.remote}\033\\{platform_icon}\033]8;;\033\\ ]")

    return SegmentGenerationResult(
        line=1,
        index=0,
        segment=Segment(text=" ".join(parts)),
        generator="internal.git",
        cache_duration=TimeDelta(seconds=5),
    )
