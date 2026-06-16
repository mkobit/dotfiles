import asyncio
import json
import logging
import os
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

import typer
from pydantic import TypeAdapter, ValidationError
from whenever import Instant

from termstatus.cache import SegmentCache
from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payload import StatusLineStdIn
from termstatus.payloads.antigravity import AntigravityPayload
from termstatus.render import probe_terminal_width, render_lines
from termstatus.segments.antigravity import format_agent_state, format_vcs_info, format_workspace_info, generate_title
from termstatus.segments.antigravity import format_context_usage as ag_format_context_usage
from termstatus.segments.antigravity import format_model_info as ag_format_model_info
from termstatus.segments.chezmoi import detect_chezmoi_root, generate_chezmoi_segment
from termstatus.segments.claude import (
    format_context_usage,
    format_cost,
    format_lines_impact,
    format_model_info,
    format_session_info,
)
from termstatus.segments.git import generate_git_segment
from termstatus.segments.workspace import format_directory, format_obsidian_vault

logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

cli = typer.Typer(add_completion=False)

antigravity_app = typer.Typer()
cli.add_typer(antigravity_app, name="antigravity")


@antigravity_app.command("render")
def antigravity_render():
    raw_json_str = "{}"
    try:
        if not sys.stdin.isatty():
            raw_json_str = sys.stdin.read()
            raw_data = json.loads(raw_json_str) if raw_json_str.strip() else {}
        else:
            raw_data = {}
    except Exception as e:
        logger.debug(f"Failed to read/parse stdin: {e}")
        raw_data = {}

    try:
        payload = AntigravityPayload(**raw_data)
    except Exception as e:
        logger.debug(f"Failed to validate payload: {e}")
        payload = AntigravityPayload()

    all_segments: list[SegmentGenerationResult] = []

    try:
        all_segments.extend(format_agent_state(payload))
        all_segments.extend(ag_format_model_info(payload))
        all_segments.extend(format_workspace_info(payload))
        all_segments.extend(format_vcs_info(payload))
        all_segments.extend(ag_format_context_usage(payload))
    except Exception as e:
        logger.warning(f"Error generating segments: {e}")

    width = asyncio.run(probe_terminal_width())
    lines = render_lines(None, None, all_segments, terminal_width=width)

    for line in lines:
        print(line)


@antigravity_app.command("title")
def antigravity_title():
    raw_json_str = "{}"
    try:
        if not sys.stdin.isatty():
            raw_json_str = sys.stdin.read()
            raw_data = json.loads(raw_json_str) if raw_json_str.strip() else {}
        else:
            raw_data = {}
    except Exception as e:
        logger.debug(f"Failed to read/parse stdin: {e}")
        raw_data = {}

    try:
        payload = AntigravityPayload(**raw_data)
    except Exception as e:
        logger.debug(f"Failed to validate payload: {e}")
        payload = AntigravityPayload()

    title = generate_title(payload)
    print(title)


SEGMENT_GENERATION_ADAPTER = TypeAdapter(list[SegmentGenerationResult] | SegmentGenerationResult)


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
            stdout, _stderr = await asyncio.wait_for(proc.communicate(input=payload_json.encode()), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.communicate()
            logger.warning(f"Timeout error in external generator {cmd}")
            return []

        if proc.returncode == 0 and stdout.strip():
            try:
                data = SEGMENT_GENERATION_ADAPTER.validate_json(stdout)

                results = data if isinstance(data, list) else [data]

                for item in results:
                    item.generator = cmd
                return results

            except ValidationError as e:
                logger.warning(f"Validation error in external generator {cmd}: {e}")
                return []
            except Exception as e:
                logger.warning(f"JSON parsing error in external generator {cmd}: {e}")
                return []
        elif proc.returncode != 0:
            logger.warning(f"External generator {cmd} exited with code {proc.returncode}")
            raise Exception(f"Exit code {proc.returncode}") from None
    except Exception as e:
        logger.warning(f"Error running external generator {cmd}: {e}")
        raise
    return []


claude_app = typer.Typer()
cli.add_typer(claude_app, name="claude")


@claude_app.command("render")
def claude_render(  # noqa: C901
    generator: Annotated[
        list[str] | None, typer.Option(help="External command or script to generate segments (takes JSON on stdin).")
    ] = None,
    show_errors: Annotated[
        bool, typer.Option("--show-errors", help="Display error segments for failed generators.")
    ] = False,
) -> None:
    generator_tuple = tuple(generator) if generator else ()

    raw_json_str = "{}"
    try:
        if not sys.stdin.isatty():
            raw_json_str = sys.stdin.read()
            raw_data = json.loads(raw_json_str) if raw_json_str.strip() else {}
        else:
            raw_data = {}
    except Exception as e:
        logger.debug(f"Failed to read/parse stdin: {e}")
        raw_data = {}

    try:
        payload = StatusLineStdIn(**raw_data)
    except Exception as e:
        logger.debug(f"Failed to validate payload: {e}")
        payload = StatusLineStdIn()

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()
    is_worktree = bool(payload.workspace.git_worktree)

    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        cache_path = Path(xdg_cache_home) / "termstatus" / "cache.json"
    else:
        cache_path = Path.home() / ".cache" / "termstatus" / "cache.json"
    cache = SegmentCache(cache_path)
    cache.load()
    all_segments: list[SegmentGenerationResult] = []
    tasks = []

    def handle_error(err: Exception, name: str) -> list[SegmentGenerationResult]:
        if show_errors:
            return [
                SegmentGenerationResult(
                    line=3,
                    index=999,
                    generator=name,
                    segment=Segment(text=f"[Error: {name}]"),
                )
            ]
        return []

    terminal_width: int | None = None

    async def fetch_all() -> None:  # noqa: C901
        nonlocal all_segments, terminal_width
        chezmoi_root = detect_chezmoi_root(cwd)
        git_key = f"internal.chezmoi:{cwd.resolve()}" if chezmoi_root else f"internal.git:{cwd.resolve()}"
        cached_git = await cache.get(git_key)
        if cached_git is not None:
            all_segments = all_segments + cached_git
        else:

            async def wrap_git():
                try:
                    if chezmoi_root:
                        res = await generate_chezmoi_segment(cwd, chezmoi_root)
                    else:
                        res = await generate_git_segment(cwd, is_worktree)
                    return ("git", git_key, res)
                except Exception as e:
                    return ("git", git_key, e)

            tasks.append(wrap_git())

        for cmd in generator_tuple:
            cmd_key = f"external:{cmd}"
            cached_cmd = await cache.get(cmd_key)
            if cached_cmd is not None:
                all_segments = all_segments + cached_cmd
            else:

                async def wrap_cmd(c=cmd, ck=cmd_key):
                    try:
                        res = await run_external_generator(c, raw_json_str)
                        return ("external", ck, res)
                    except Exception as e:
                        return ("external", ck, e)

                tasks.append(wrap_cmd())

        # Probe terminal width concurrently with segment generation
        width_task = asyncio.create_task(probe_terminal_width())
        results = await asyncio.gather(*tasks)
        terminal_width = await width_task

        cache_updates = []
        for _, key, res in results:
            if isinstance(res, Exception):
                all_segments = all_segments + handle_error(res, key)
            else:
                all_segments = all_segments + res
                if res:
                    try:
                        if any(hasattr(r, "cache_duration") and r.cache_duration for r in res):
                            duration = next(
                                (r.cache_duration for r in res if hasattr(r, "cache_duration") and r.cache_duration),
                                None,
                            )
                            if duration:
                                cache_updates.append((key, list(res), Instant.now() + duration))
                    except Exception as e:
                        logger.debug(f"Failed to set cache for {key}: {e}")

        if cache_updates:
            try:
                await cache.set_many(cache_updates)
            except Exception as e:
                logger.debug(f"Failed to set batch cache: {e}")

    asyncio.run(fetch_all())

    try:
        internal_results_nested = [
            format_model_info(payload),
            format_session_info(payload),
            format_directory(cwd),
            format_obsidian_vault(cwd),
            format_context_usage(payload.context_window),
            format_cost(payload),
            format_lines_impact(payload),
        ]
        for result_list in internal_results_nested:
            all_segments = all_segments + result_list
    except Exception as e:
        all_segments = all_segments + handle_error(e, "internal.claude_or_workspace")

    lines = render_lines(payload, None, all_segments, terminal_width=terminal_width)

    for line in lines:
        print(line)


if __name__ == "__main__":
    cli()
