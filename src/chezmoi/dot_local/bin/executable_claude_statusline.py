#!/usr/bin/env python3
import json
import sys
import subprocess
import time
import hashlib
import tempfile
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Nerd Font Icons (Unicode Escape Sequences)
ICON_BRANCH = "\uf418"  # 
ICON_DIRTY = "\u2717"  # ✗
ICON_STAGED = "\u271a"  # ✚
ICON_CLEAN = "\u2714"  # ✔
ICON_REMOTE = "\uf0c2"  # 
ICON_CONTEXT_EMOJI = "\U0001f9e0"
ICON_TIME = "\u23f1\ufe0f"  # ⏱️
ICON_UNKNOWN = "\uf128"  # 

# Block characters for visual progress bar
BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░

CACHE_DURATION = 30  # seconds

# https://code.claude.com/docs/en/statusline


@dataclass(frozen=True)
class GitInfo:
    branch: str
    remote: str | None
    dirty: bool
    staged: bool
    ahead: int
    behind: int
    is_repo: bool


@dataclass(frozen=True)
class StatusData:
    model_name: str
    agent_name: str | None
    cwd: Path
    context_used_pct: int | float | None
    git: GitInfo | None


def get_git_info(cwd: Path) -> GitInfo | None:
    """Retrieves git information for the given directory."""
    # Convert Path to absolute string for consistency
    cwd_str = str(cwd.resolve())
    cache_key = hashlib.md5(cwd_str.encode()).hexdigest()
    cache_file = Path(tempfile.gettempdir()) / f"claude_statusline_git_{cache_key}.json"

    # Check cache
    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < CACHE_DURATION:
                with cache_file.open("r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return GitInfo(**data)
        except (OSError, json.JSONDecodeError, TypeError):
            pass  # Ignore cache errors and re-fetch

    # Fetch fresh data
    try:
        # Check if git repo
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None

    branch = "HEAD"
    remote = None
    dirty = False
    staged = False
    ahead = 0
    behind = 0
    is_repo = True

    try:
        # Branch name and Remote URL
        # We can optimize by combining these checks or just keeping them separate as they are fast.
        # But 'git remote get-url' might fail if no remote, so keep it separate.
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        # Remote URL
        try:
            remote_url = subprocess.check_output(
                ["git", "ls-remote", "--get-url", "origin"],
                cwd=cwd,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            # Convert SSH to HTTPS for clickable links if needed
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace(":", "/").replace("git@", "https://")
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            remote = remote_url
        except subprocess.CalledProcessError:
            pass

        # Status (staged/dirty)
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        if status_output:
            for line in status_output.splitlines():
                if (
                    line.startswith("??") or line[1] != " "
                ):  # Untracked or Modified working tree
                    dirty = True
                if line[0] != " " and line[0] != "?":  # Staged
                    staged = True

        # Ahead/Behind
        # Only check if we have a tracking branch
        try:
            rev_list = subprocess.check_output(
                ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
                cwd=cwd,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            a, b = map(int, rev_list.split())
            ahead = a
            behind = b
        except subprocess.CalledProcessError:
            pass

    except Exception:
        pass

    info = GitInfo(
        branch=branch,
        remote=remote,
        dirty=dirty,
        staged=staged,
        ahead=ahead,
        behind=behind,
        is_repo=is_repo,
    )

    # Save cache
    try:
        with cache_file.open("w") as f:
            json.dump(asdict(info), f)
    except OSError:
        pass

    return info


def format_context_usage(used_pct: int | float | None) -> str:
    """Formats the context usage with color and visual indicator."""
    if used_pct is None:
        return f"{ICON_UNKNOWN} {CYAN}?%{RESET}"

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 70:
        color = YELLOW

    # Visual indicator (10 blocks)
    # 0-10% -> 1 block, etc.
    blocks = min(int(used_pct // 10), 10)
    visual_bar = (BLOCK_FILLED * blocks) + (BLOCK_EMPTY * (10 - blocks))

    return f"{ICON_CONTEXT_EMOJI} {color}{visual_bar} {used_pct}%{RESET}"


def format_git_branch(info: GitInfo) -> str:
    return f"{ICON_BRANCH} {info.branch}"


def format_git_state(info: GitInfo) -> str:
    # Use functional construction with filter
    parts = [
        f"{RED}{ICON_DIRTY}{RESET}" if info.dirty else None,
        f"{YELLOW}{ICON_STAGED}{RESET}" if info.staged else None,
    ]
    # Filter out None values
    valid_parts = list(filter(None, parts))

    # Default to clean if no other state
    if not valid_parts:
        return f"{GREEN}{ICON_CLEAN}{RESET}"

    return "".join(valid_parts)


def format_git_ahead_behind(info: GitInfo) -> str:
    parts = [
        f"↑{info.ahead}" if info.ahead > 0 else None,
        f"↓{info.behind}" if info.behind > 0 else None,
    ]
    return " ".join(filter(None, parts))


def format_git_remote(info: GitInfo) -> str:
    if not info.remote:
        return ""
    return f"\033]8;;{info.remote}\033\\{ICON_REMOTE}\033]8;;\033\\"


def format_git_status(info: GitInfo | None) -> str:
    """Formats the git status string using helper functions."""
    if not info:
        return ""

    parts = [
        format_git_branch(info),
        format_git_state(info),
        format_git_ahead_behind(info),
        format_git_remote(info),
    ]
    return " ".join(filter(None, parts))


def format_model_info(data: StatusData) -> str:
    parts = [
        f"{BOLD}{BLUE}[{data.model_name}]{RESET}",
        f"{MAGENTA}({data.agent_name}){RESET}" if data.agent_name else None,
    ]
    return " ".join(filter(None, parts))


def format_cwd_link(data: StatusData) -> str:
    try:
        display_path = str(data.cwd.relative_to(Path.home()))
        if display_path == ".":
            display_path = "~"
        else:
            display_path = f"~/{display_path}"
    except ValueError:
        display_path = str(data.cwd)

    cwd_link = f"\033]8;;file://{data.cwd}\033\\{display_path}\033]8;;\033\\"
    return f"\U0001f4c1 {cwd_link}"


def main() -> None:
    try:
        # Read JSON from stdin
        if not sys.stdin.isatty():
            raw_data = json.load(sys.stdin)
        else:
            # Fallback for manual testing
            raw_data = {}
    except json.JSONDecodeError:
        raw_data = {}

    cwd_str = raw_data.get("workspace", {}).get("current_dir") or str(Path.cwd())
    cwd = Path(cwd_str).resolve()
    context = raw_data.get("context_window", {})
    used_pct = context.get("used_percentage")

    status_data = StatusData(
        model_name=raw_data.get("model", {}).get("display_name", "Unknown Model"),
        agent_name=raw_data.get("agent", {}).get("name"),
        cwd=cwd,
        context_used_pct=used_pct,
        git=get_git_info(cwd),
    )

    # Format Output
    # Line 1: Model | Agent (if present) | CWD Link | Context
    line1 = " ".join(
        filter(
            None,
            [
                format_model_info(status_data),
                format_cwd_link(status_data),
                format_context_usage(status_data.context_used_pct),
            ],
        )
    )
    print(line1)

    # Line 2: Git Status (if applicable)
    if status_data.git:
        print(format_git_status(status_data.git))


if __name__ == "__main__":
    main()
