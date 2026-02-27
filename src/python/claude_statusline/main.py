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
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Nerd Font Icons (Unicode Escape Sequences)
ICON_BRANCH = "\uf418"  # 
ICON_DIRTY = "\uf00d"  # 
ICON_STAGED = "\uf067"  # 
ICON_UNTRACKED = "\uf128"  # 
ICON_CLEAN = "\uf00c"  # 
ICON_REMOTE = "\uf0c2"  # 
ICON_DIR = "\uf07c"  # 

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
    untracked: bool
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
    session_name: str | None
    session_id: str | None
    cost_usd: float | None


def get_git_info(cwd: Path) -> GitInfo | None:
    """Retrieves git information for the given directory."""
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
            pass

    # Quick check if git repo
    try:
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
    untracked = False
    ahead = 0
    behind = 0
    is_repo = True

    try:
        # Branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        # Remote
        try:
            remote_url = subprocess.check_output(
                ["git", "ls-remote", "--get-url", "origin"],
                cwd=cwd,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace(":", "/").replace("git@", "https://")
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            remote = remote_url
        except subprocess.CalledProcessError:
            pass

        # Status
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        if status_output:
            lines = status_output.splitlines()
            staged = any(line[0] not in (" ", "?") for line in lines)
            dirty = any(line[1] != " " and not line.startswith("??") for line in lines)
            untracked = any(line.startswith("??") for line in lines)

        # Ahead/Behind
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
        untracked=untracked,
        ahead=ahead,
        behind=behind,
        is_repo=is_repo,
    )

    try:
        with cache_file.open("w") as f:
            json.dump(asdict(info), f)
    except OSError:
        pass

    return info


def format_context_usage(used_pct: int | float | None) -> str:
    """Formats the context usage with a block-based progress bar."""
    if used_pct is None:
        used_pct = 0.0

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 50:
        color = YELLOW

    width = 10
    filled = min(int(width * (used_pct / 100)), width)
    visual_bar = (BLOCK_FILLED * filled) + (BLOCK_EMPTY * (width - filled))

    return f"{DIM}ctx:{RESET} {color}{visual_bar}{RESET} {int(used_pct)}%"


def format_model_info(data: StatusData) -> str:
    parts = [
        f"{BLUE}{BOLD}{data.model_name}{RESET}",
        f"{MAGENTA}@{data.agent_name}{RESET}" if data.agent_name else None,
    ]
    return " ".join(filter(None, parts))


def format_session_info(data: StatusData) -> str:
    if data.session_name:
        return f"{CYAN}#{data.session_name}{RESET}"
    if data.session_id:
        # Show first 8 chars of ID
        return f"{DIM}#{data.session_id[:8]}{RESET}"
    return ""


def format_cost(data: StatusData) -> str:
    if data.cost_usd is None:
        return ""
    return f"{GREEN}${data.cost_usd:.2f}{RESET}"


def shorten_path(path: Path) -> str:
    """Shortens the path for display (e.g. ~/projects/foo -> .../projects/foo)."""
    try:
        rel_path = path.relative_to(Path.home())
        parts = list(rel_path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        if str(rel_path) == ".":
            return "~"
        return f"~/{rel_path}"
    except ValueError:
        parts = list(path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        return str(path)


def format_directory(data: StatusData) -> str:
    display_path = shorten_path(data.cwd)
    cwd_link = f"\033]8;;file://{data.cwd}\033\\{display_path}\033]8;;\033\\"
    return f"{BLUE}{ICON_DIR} {cwd_link}{RESET}"


def format_git_full(info: GitInfo | None) -> str:
    if not info:
        return ""

    # Branch
    parts = [f"{MAGENTA}{ICON_BRANCH} {info.branch}{RESET}"]

    # Status Icons
    status_parts = []
    if info.dirty:
        status_parts.append(f"{RED}{ICON_DIRTY}{RESET}")
    if info.staged:
        status_parts.append(f"{YELLOW}{ICON_STAGED}{RESET}")
    if info.untracked:
        status_parts.append(f"{CYAN}{ICON_UNTRACKED}{RESET}")

    if not status_parts:
        status_parts.append(f"{GREEN}{ICON_CLEAN}{RESET}")

    parts.append("".join(status_parts))

    # Ahead/Behind
    if info.ahead > 0:
        parts.append(f"{GREEN}↑{info.ahead}{RESET}")
    if info.behind > 0:
        parts.append(f"{RED}↓{info.behind}{RESET}")

    # Remote Link (icon only)
    if info.remote:
        parts.append(f"\033]8;;{info.remote}\033\\{ICON_REMOTE}\033]8;;\033\\")

    return " ".join(parts)


def main() -> None:
    try:
        # Read JSON from stdin
        if not sys.stdin.isatty():
            # For debugging, one might want to dump to a file here
            # with open('/tmp/claude_input.json', 'w') as f:
            #     f.write(sys.stdin.read())
            # sys.stdin.seek(0)
            raw_data = json.load(sys.stdin)
        else:
            raw_data = {}
    except json.JSONDecodeError:
        raw_data = {}

    cwd_str = raw_data.get("workspace", {}).get("current_dir") or str(Path.cwd())
    cwd = Path(cwd_str).resolve()

    context = raw_data.get("context_window", {})
    used_pct = context.get("used_percentage")

    cost = raw_data.get("cost", {})
    cost_usd = cost.get("total_cost_usd")

    status_data = StatusData(
        model_name=raw_data.get("model", {}).get("display_name", "Unknown Model"),
        agent_name=raw_data.get("agent", {}).get("name"),
        cwd=cwd,
        context_used_pct=used_pct,
        git=get_git_info(cwd),
        session_name=raw_data.get("session_name"),
        session_id=raw_data.get("session_id"),
        cost_usd=cost_usd,
    )

    # Line 1: [Model] (Agent) [Context] #Session $Cost
    line1_parts = [
        format_model_info(status_data),
        format_context_usage(status_data.context_used_pct),
        format_session_info(status_data),
        format_cost(status_data),
    ]
    print(" ".join(filter(None, line1_parts)))

    # Line 2: [Dir] [Git Info]
    line2_parts = [
        format_directory(status_data),
        format_git_full(status_data.git),
    ]
    print(" ".join(filter(None, line2_parts)))


if __name__ == "__main__":
    main()
