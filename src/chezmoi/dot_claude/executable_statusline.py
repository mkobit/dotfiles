#!/usr/bin/env python3
import json
import sys
import os
import subprocess
import time
import hashlib
import tempfile
from typing import Dict, Any, Optional, Union

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

# Nerd Font Icons
ICON_BRANCH = ""
ICON_DIRTY = "✗"
ICON_STAGED = "✚"
ICON_CLEAN = "✔"
ICON_REMOTE = ""
ICON_CONTEXT = "🧠"
ICON_TIME = "⏱️"
ICON_UNKNOWN = "?"

CACHE_DURATION = 30  # seconds

def get_git_info(cwd: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves git information for the given directory.
    Returns a dictionary with branch, status, remote, ahead, behind.
    """
    cache_key = hashlib.md5(cwd.encode()).hexdigest()
    cache_file = os.path.join(tempfile.gettempdir(), f"claude_statusline_git_{cache_key}.json")

    # Check cache
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < CACHE_DURATION:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                         return data
        except (OSError, json.JSONDecodeError):
            pass  # Ignore cache errors and re-fetch

    # Fetch fresh data
    try:
        # Check if git repo
        subprocess.check_output(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            cwd=cwd, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return None

    info: Dict[str, Any] = {
        'branch': 'HEAD',
        'remote': None,
        'dirty': False,
        'staged': False,
        'ahead': 0,
        'behind': 0,
        'is_repo': True
    }

    try:
        # Branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
        info['branch'] = branch

        # Remote URL
        try:
            remote_url = subprocess.check_output(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=cwd, text=True, stderr=subprocess.DEVNULL
            ).strip()
            # Convert SSH to HTTPS for clickable links if needed
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace(":", "/").replace("git@", "https://")
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            info['remote'] = remote_url
        except subprocess.CalledProcessError:
            pass

        # Status (staged/dirty)
        status_output = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            cwd=cwd, text=True, stderr=subprocess.DEVNULL
        )
        if status_output:
            for line in status_output.splitlines():
                if line.startswith('??') or line[1] != ' ': # Untracked or Modified working tree
                    info['dirty'] = True
                if line[0] != ' ' and line[0] != '?': # Staged
                    info['staged'] = True

        # Ahead/Behind
        # Only check if we have a tracking branch
        try:
            rev_list = subprocess.check_output(
                ['git', 'rev-list', '--left-right', '--count', 'HEAD...@{u}'],
                cwd=cwd, text=True, stderr=subprocess.DEVNULL
            ).strip()
            ahead, behind = map(int, rev_list.split())
            info['ahead'] = ahead
            info['behind'] = behind
        except subprocess.CalledProcessError:
            pass

    except Exception:
        pass

    # Save cache
    try:
        with open(cache_file, 'w') as f:
            json.dump(info, f)
    except OSError:
        pass

    return info

def format_context_usage(used_pct: Optional[Union[int, float]]) -> str:
    """Formats the context usage with color."""
    if used_pct is None:
        return f"{ICON_CONTEXT} {CYAN}?%{RESET}"

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 70:
        color = YELLOW

    return f"{ICON_CONTEXT} {color}{used_pct}%{RESET}"

def format_git_status(info: Optional[Dict[str, Any]]) -> str:
    """Formats the git status string."""
    if not info:
        return ""

    parts = []

    # Branch
    branch_str = f"{ICON_BRANCH} {info['branch']}"
    parts.append(branch_str)

    # Status icons
    status_icons = []
    if info['dirty']:
        status_icons.append(f"{RED}{ICON_DIRTY}{RESET}")
    if info['staged']:
        status_icons.append(f"{YELLOW}{ICON_STAGED}{RESET}")

    if not status_icons:
        status_icons.append(f"{GREEN}{ICON_CLEAN}{RESET}")

    parts.extend(status_icons)

    # Ahead/Behind
    if info['ahead'] > 0:
        parts.append(f"↑{info['ahead']}")
    if info['behind'] > 0:
        parts.append(f"↓{info['behind']}")

    # Remote Link (OSC 8)
    if info['remote']:
        # We don't display the URL, but maybe we can make the branch name clickable?
        # Or add a cloud icon that links to it.
        link = f"\033]8;;{info['remote']}\033\\{ICON_REMOTE}\033]8;;\033\\"
        parts.append(link)

    return " ".join(parts)

def main() -> None:
    try:
        # Read JSON from stdin
        if not sys.stdin.isatty():
            data = json.load(sys.stdin)
        else:
            # Fallback for manual testing
            data = {}
    except json.JSONDecodeError:
        data = {}

    # Extract Data
    model_name = data.get('model', {}).get('display_name', 'Unknown Model')
    agent_name = data.get('agent', {}).get('name')
    cwd = data.get('workspace', {}).get('current_dir') or os.getcwd()

    context = data.get('context_window', {})
    used_pct = context.get('used_percentage')
    if used_pct is None and 'current_usage' in context:
        # Calculate manually if needed, but 'used_percentage' is usually pre-calc
        pass

    # Get Git Info
    git_info = get_git_info(cwd)

    # Format Output

    # Line 1: Model | Agent (if present) | CWD Link | Context
    line1_parts = []
    line1_parts.append(f"{BOLD}{BLUE}[{model_name}]{RESET}")

    if agent_name:
        line1_parts.append(f"{MAGENTA}({agent_name}){RESET}")

    # CWD Link
    cwd_name = os.path.basename(cwd) or cwd
    cwd_link = f"\033]8;;file://{cwd}\033\\{cwd_name}\033]8;;\033\\"
    line1_parts.append(f"📁 {cwd_link}")

    # Context
    line1_parts.append(format_context_usage(used_pct))

    print(" ".join(line1_parts))

    # Line 2: Git Status (if applicable)
    if git_info:
        git_str = format_git_status(git_info)
        print(f"{git_str}")

if __name__ == "__main__":
    main()
