#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, Field

# --- Terminal Escape Sequences ---
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
BG_DIM = "\033[100m"


# --- Icons & Fallbacks ---
def has_nerd_fonts() -> bool:
    """Checks if we likely have nerd fonts available based on environment."""
    term = os.environ.get("TERM", "")

    # Kitty, Wezterm, Ghostty usually have good font support
    if "kitty" in term or "wezterm" in term or "ghostty" in term:
        return True

    # Otherwise fallback to basic unicode unless NERD_FONT is explicitly set
    return os.environ.get("NERD_FONT", "0") == "1"


USE_ICONS = has_nerd_fonts()

ICON_BRANCH = "\uf418" if USE_ICONS else "⎇"
ICON_DIRTY = "\uf00d" if USE_ICONS else "✗"
ICON_STAGED = "\uf067" if USE_ICONS else "+"
ICON_UNTRACKED = "\uf128" if USE_ICONS else "?"
ICON_CLEAN = "\uf00c" if USE_ICONS else "✓"
ICON_REMOTE = "\uf0c2" if USE_ICONS else "☁"
ICON_DIR = "\uf07c" if USE_ICONS else "📂"
ICON_TIMER = "\u23f2" if USE_ICONS else "⏱"
ICON_COST = "\uf155" if USE_ICONS else "$"
ICON_TOKENS = "\uf4a5" if USE_ICONS else "⚡"
ICON_ROBOT = "\uf544" if USE_ICONS else "🤖"
ICON_WORKTREE = "\uf1bb" if USE_ICONS else "🌳"

BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░
DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "

CACHE_DURATION = 30  # seconds

# --- Pydantic Models for Claude Code JSON Payload ---
# See: https://code.claude.com/docs/en/statusline


class ModelInfo(BaseModel):
    display_name: str = "Unknown Model"


class WorkspaceInfo(BaseModel):
    current_dir: str = Field(default_factory=lambda: str(Path.cwd()))


class ContextWindowInfo(BaseModel):
    used_percentage: float | None = 0.0
    total_tokens: int | None = 0
    used_tokens: int | None = 0
    cache_creation_input_tokens: int | None = 0
    cache_read_input_tokens: int | None = 0


class CostInfo(BaseModel):
    total_cost_usd: float | None = 0.0


class AgentInfo(BaseModel):
    name: str | None = None


class ClaudePayload(BaseModel):
    model: ModelInfo = Field(default_factory=ModelInfo)
    workspace: WorkspaceInfo = Field(default_factory=WorkspaceInfo)
    context_window: ContextWindowInfo = Field(default_factory=ContextWindowInfo)
    session_name: str | None = None
    session_id: str | None = None
    cost: CostInfo = Field(default_factory=CostInfo)
    agent: AgentInfo = Field(default_factory=AgentInfo)


# --- Internal Data Models ---
class GitInfo(BaseModel):
    branch: str
    remote: str | None
    dirty: bool
    staged: bool
    untracked: bool
    ahead: int
    behind: int
    is_repo: bool
    is_worktree: bool = False


def get_git_info(cwd: Path) -> GitInfo | None:
    """Retrieves git information for the given directory with caching."""
    cwd_str = str(cwd.resolve())
    cache_key = hashlib.md5(cwd_str.encode()).hexdigest()
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
    is_worktree = False

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        # Check if we are in a git worktree
        try:
            git_dir = subprocess.check_output(
                ["git", "rev-parse", "--absolute-git-dir"],
                cwd=cwd,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if "/worktrees/" in git_dir:
                is_worktree = True
        except subprocess.CalledProcessError:
            pass

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
        is_worktree=is_worktree,
    )

    try:
        with cache_file.open("w") as f:
            json.dump(info.model_dump(), f)
    except OSError:
        pass

    return info


def get_session_timer(session_id: str | None) -> str:
    """Calculates and formats session duration based on session_id."""
    if not session_id:
        return ""

    timer_file = Path(tempfile.gettempdir()) / f"claude_session_timer_{session_id}.txt"
    now = time.time()

    try:
        if not timer_file.exists():
            with timer_file.open("w") as f:
                f.write(str(now))
            start_time = now
        else:
            with timer_file.open("r") as f:
                start_time = float(f.read().strip())
    except OSError, ValueError:
        start_time = now

    elapsed_seconds = int(now - start_time)
    td = timedelta(seconds=elapsed_seconds)

    # Format: HH:MM:SS
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


# --- Formatting Helpers ---


def format_context_usage(cw: ContextWindowInfo) -> str:
    """Formats the context usage with a block-based progress bar and token stats."""
    used_pct = cw.used_percentage or 0.0

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 50:
        color = YELLOW

    width = 10
    filled = min(int(width * (used_pct / 100)), width)
    visual_bar = (BLOCK_FILLED * filled) + (BLOCK_EMPTY * (width - filled))

    # Add caching info if available
    cache_info = ""
    cached_tokens = (cw.cache_creation_input_tokens or 0) + (
        cw.cache_read_input_tokens or 0
    )
    if cached_tokens > 0:
        if cached_tokens > 1000000:
            cache_info = f" {CYAN}({cached_tokens / 1000000:.1f}M cache){RESET}"
        elif cached_tokens > 1000:
            cache_info = f" {CYAN}({cached_tokens / 1000:.1f}k cache){RESET}"

    return f"{DIM}ctx:{RESET} {color}{visual_bar}{RESET} {int(used_pct)}%{cache_info}"


def format_model_info(payload: ClaudePayload) -> str:
    parts = [
        f"{ICON_ROBOT} {BLUE}{BOLD}{payload.model.display_name}{RESET}",
        f"{MAGENTA}@{payload.agent.name}{RESET}" if payload.agent.name else None,
    ]
    return " ".join(filter(None, parts))


def format_session_info(payload: ClaudePayload) -> str:
    parts = []
    if payload.session_name:
        parts.append(f"{CYAN}#{payload.session_name}{RESET}")
    elif payload.session_id:
        parts.append(f"{DIM}#{payload.session_id[:8]}{RESET}")

    timer = get_session_timer(payload.session_id)
    if timer:
        parts.append(f"{YELLOW}{ICON_TIMER} {timer}{RESET}")

    return DIVIDER_BAR.join(parts)


def format_cost(payload: ClaudePayload) -> str:
    if not payload.cost.total_cost_usd:
        return ""
    return f"{GREEN}{ICON_COST}{payload.cost.total_cost_usd:.2f}{RESET}"


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


def format_directory(cwd: Path) -> str:
    display_path = shorten_path(cwd)
    cwd_link = f"\033]8;;file://{cwd}\033\\{display_path}\033]8;;\033\\"
    return f"{BLUE}{ICON_DIR} {cwd_link}{RESET}"


def format_git_full(info: GitInfo | None) -> str:
    if not info:
        return ""

    branch_icon = ICON_WORKTREE if info.is_worktree else ICON_BRANCH
    parts = [f"{MAGENTA}{branch_icon} {info.branch}{RESET}"]

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

    if info.ahead > 0:
        parts.append(f"{GREEN}↑{info.ahead}{RESET}")
    if info.behind > 0:
        parts.append(f"{RED}↓{info.behind}{RESET}")

    if info.remote:
        parts.append(f"\033]8;;{info.remote}\033\\{ICON_REMOTE}\033]8;;\033\\")

    return " ".join(parts)


def main() -> None:
    try:
        if not sys.stdin.isatty():
            raw_data = json.load(sys.stdin)
        else:
            raw_data = {}
    except json.JSONDecodeError:
        raw_data = {}

    try:
        payload = ClaudePayload(**raw_data)
    except Exception:
        # Fallback if parsing completely fails, though defaults should catch most
        payload = ClaudePayload()

    cwd = Path(payload.workspace.current_dir).resolve()
    git_info = get_git_info(cwd)

    # --- Line 1: AI Session & Cost ---
    line1_left = (
        f"{format_model_info(payload)} {DIVIDER_BAR} {format_session_info(payload)}"
    )
    line1_right_parts = [
        format_context_usage(payload.context_window),
        format_cost(payload),
    ]
    line1_right = f" {DIVIDER_BAR} ".join(filter(None, line1_right_parts))
    print(f"{line1_left} {line1_right}")

    # --- Line 2: Environment & Git ---
    line2_left_parts = [format_directory(cwd), format_git_full(git_info)]
    line2_left = f" {DIVIDER_DOT} ".join(filter(None, line2_left_parts))
    print(line2_left)


if __name__ == "__main__":
    main()
