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

from claude_statusline.cache import SegmentCache
from claude_statusline.render import render_lines
from claude_statusline.segments.claude import (
    format_context_usage,
    format_cost,
    format_model_info,
    format_session_info,
)
from claude_statusline.segments.git import generate_git_segment
from claude_statusline.segments.workspace import format_directory, format_obsidian_vault
from claude_statusline.types.layout import Segment, SegmentGenerationResult
from claude_statusline.types.payload import StatusLineStdIn

logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

cli = typer.Typer(add_completion=False)

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


@cli.command()
def main(  # noqa: C901
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
        cache_path = Path(xdg_cache_home) / "claude_statusline" / "cache.json"
    else:
        cache_path = Path.home() / ".cache" / "claude_statusline" / "cache.json"
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

    async def fetch_all() -> None:  # noqa: C901
        git_key = f"internal.git:{cwd.resolve()}"
        cached_git = await cache.get(git_key)
        if cached_git is not None:
            all_segments.extend(cached_git)
        else:

            async def wrap_git():
                try:
                    res = await generate_git_segment(cwd, is_worktree)
                    return ("git", git_key, res)
                except Exception as e:
                    return ("git", git_key, e)

            tasks.append(wrap_git())

        for cmd in generator_tuple:
            cmd_key = f"external:{cmd}"
            cached_cmd = await cache.get(cmd_key)
            if cached_cmd is not None:
                all_segments.extend(cached_cmd)
            else:

                async def wrap_cmd(c=cmd, ck=cmd_key):
                    try:
                        res = await run_external_generator(c, raw_json_str)
                        return ("external", ck, res)
                    except Exception as e:
                        return ("external", ck, e)

                tasks.append(wrap_cmd())

        results = await asyncio.gather(*tasks)

        cache_updates = []
        for _, key, res in results:
            if isinstance(res, Exception):
                all_segments.extend(handle_error(res, key))
            else:
                all_segments.extend(res)
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
        internal_results = [
            format_model_info(payload),
            format_session_info(payload),
            format_directory(cwd),
            format_obsidian_vault(cwd),
            format_context_usage(payload.context_window),
            format_cost(payload),
        ]
        all_segments.extend([r for r in internal_results if r])
    except Exception as e:
        all_segments.extend(handle_error(e, "internal.claude_or_workspace"))

    lines = render_lines(payload, None, all_segments)

    for line in lines:
        print(line)


if __name__ == "__main__":
    cli()
