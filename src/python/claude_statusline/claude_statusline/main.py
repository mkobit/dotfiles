import asyncio
import hashlib
import json
import logging
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import click
from pydantic import TypeAdapter, ValidationError

from claude_statusline.models import GitInfo, SegmentGenerationResult, StatusLineStdIn
from claude_statusline.render import render_lines

CACHE_DURATION = 30  # seconds

logging.basicConfig(
    level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s"
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


def _check_is_repo(cwd: Path) -> bool:
    res = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip() == "true"
    return False


def _get_branch_and_remote(cwd: Path) -> BranchRemoteInfo:
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

    return BranchRemoteInfo(branch=branch, remote=remote)


def _get_status(cwd: Path) -> GitStatusInfo:
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

    return GitStatusInfo(dirty=dirty, staged=staged, untracked=untracked)


def _get_ahead_behind(cwd: Path) -> AheadBehindInfo:
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

    return AheadBehindInfo(ahead=ahead, behind=behind)


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

    branch_info = _get_branch_and_remote(cwd)
    status_info = _get_status(cwd)
    ahead_behind_info = _get_ahead_behind(cwd)

    info = GitInfo(
        branch=branch_info.branch,
        remote=branch_info.remote,
        dirty=status_info.dirty,
        staged=status_info.staged,
        untracked=status_info.untracked,
        ahead=ahead_behind_info.ahead,
        behind=ahead_behind_info.behind,
        is_repo=True,
        is_worktree=False,
    )

    try:
        with cache_file.open("w") as f:
            json.dump(info.model_dump(), f, indent=2)
    except OSError:
        pass

    return info


async def run_external_generator(
    cmd: str, payload_json: str, timeout: float = 2.0
) -> Sequence[SegmentGenerationResult]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *shlex.split(cmd),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=payload_json.encode()), timeout=timeout
            )
        except TimeoutError:
            proc.kill()
            await proc.communicate()
            logger.warning(f"Timeout error in external generator {cmd}")
            return []

        if proc.returncode == 0 and stdout.strip():
            try:
                adapter = TypeAdapter(
                    list[SegmentGenerationResult] | SegmentGenerationResult
                )
                data = adapter.validate_json(stdout)

                results = data if isinstance(data, list) else [data]

                # set generator name from cmd
                for item in results:
                    item.generator = cmd
                return results

            except ValidationError as e:
                logger.warning(f"Validation error in external generator {cmd}: {e}")
            except Exception as e:
                logger.warning(f"JSON parsing error in external generator {cmd}: {e}")
    except Exception as e:
        logger.warning(f"Error running external generator {cmd}: {e}")
    return []


@click.command()
@click.option(
    "--generator",
    multiple=True,
    help="External command or script to generate segments (takes JSON on stdin).",
)
def main(generator: tuple[str, ...]) -> None:
    raw_json_str = "{}"
    try:
        if not sys.stdin.isatty():
            raw_json_str = sys.stdin.read()
            raw_data = json.loads(raw_json_str) if raw_json_str.strip() else {}
        else:
            raw_data = {}
    except Exception:
        raw_data = {}

    try:
        payload = StatusLineStdIn(**raw_data)
    except Exception:
        payload = StatusLineStdIn()

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    git_info = get_git_info(cwd, payload.session_id)
    if git_info and payload.workspace.git_worktree:
        git_info.is_worktree = True

    extra_segments: list[SegmentGenerationResult] = []
    if generator:

        async def fetch_all():
            tasks = [run_external_generator(cmd, raw_json_str) for cmd in generator]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    continue
                if res:
                    extra_segments.extend(res)  # type: ignore

        asyncio.run(fetch_all())

    lines = render_lines(payload, git_info, extra_segments)

    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
