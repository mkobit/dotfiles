import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from claude_statusline.models import GitInfo, StatusLineStdIn
from claude_statusline.render import render_lines

CACHE_DURATION = 30  # seconds


def _check_is_repo(cwd: Path) -> bool:
    try:
        is_inside = subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        ).strip()
        return is_inside == b"true"
    except subprocess.CalledProcessError:
        return False


def _get_branch_and_remote(cwd: Path) -> tuple[str, str | None]:
    branch = "HEAD"
    remote = None

    branch_res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if branch_res.returncode == 0:
        branch = branch_res.stdout.strip()

    remote_res = subprocess.run(
        ["git", "ls-remote", "--get-url", "origin"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if remote_res.returncode == 0:
        remote_url = remote_res.stdout.strip()
        if remote_url.startswith("git@"):
            remote_url = remote_url.replace(":", "/").replace("git@", "https://")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        remote = remote_url

    return branch, remote


def _get_status(cwd: Path) -> tuple[bool, bool, bool]:
    dirty = False
    staged = False
    untracked = False

    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if res.returncode == 0 and res.stdout:
        lines = res.stdout.splitlines()
        staged = any(line[0] not in (" ", "?") for line in lines)
        dirty = any(line[1] != " " and not line.startswith("??") for line in lines)
        untracked = any(line.startswith("??") for line in lines)

    return dirty, staged, untracked


def _get_ahead_behind(cwd: Path) -> tuple[int, int]:
    ahead = 0
    behind = 0

    res = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if res.returncode == 0 and res.stdout:
        try:
            a, b = map(int, res.stdout.strip().split())
            ahead = a
            behind = b
        except ValueError:
            pass

    return ahead, behind


def get_git_info(cwd: Path, session_id: str | None) -> GitInfo | None:
    """Retrieves git information for the given directory with caching."""
    cwd_str = str(cwd.resolve())
    cache_key = session_id if session_id else hashlib.md5(cwd_str.encode()).hexdigest()
    cache_file = Path(tempfile.gettempdir()) / f"claude_statusline_git_{cache_key}.json"

    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < CACHE_DURATION:
                with cache_file.open("r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return GitInfo(**data)
        except OSError, json.JSONDecodeError, TypeError, ValueError:
            pass

    if not _check_is_repo(cwd):
        return None

    branch, remote = _get_branch_and_remote(cwd)
    dirty, staged, untracked = _get_status(cwd)
    ahead, behind = _get_ahead_behind(cwd)

    info = GitInfo(
        branch=branch,
        remote=remote,
        dirty=dirty,
        staged=staged,
        untracked=untracked,
        ahead=ahead,
        behind=behind,
        is_repo=True,
        is_worktree=False,
    )

    try:
        with cache_file.open("w") as f:
            json.dump(info.model_dump(), f, indent=2)
    except OSError:
        pass

    return info


def main() -> None:
    try:
        if not sys.stdin.isatty():
            raw_data = json.load(sys.stdin)
        else:
            raw_data = {}
    except json.JSONDecodeError:
        raw_data = {}

    try:
        payload = StatusLineStdIn(**raw_data)
    except Exception:
        # Fallback if parsing completely fails, though defaults should catch most
        payload = StatusLineStdIn()

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    git_info = get_git_info(cwd, payload.session_id)
    if git_info and payload.workspace.git_worktree:
        git_info.is_worktree = True

    lines = render_lines(payload, git_info)
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
