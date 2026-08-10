import asyncio
import json
import logging
import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.text import Text
from whenever import Instant

from termstatus.cache import SegmentCache
from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payload import ContextWindowInfo, CostInfo, ModelInfo, OutputStyle, StatusLineStdIn
from termstatus.render import probe_terminal_width, render_lines
from termstatus.segments.chezmoi import _format_repo, detect_chezmoi_root, generate_chezmoi_segment
from termstatus.segments.claude import (
    format_context_usage,
    format_cost,
    format_model_info,
    format_session_info,
)
from termstatus.segments.git import GitInfo, generate_git_segment
from termstatus.segments.workspace import format_directory, format_obsidian_vault

logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

cli = typer.Typer(add_completion=False)

antigravity_app = typer.Typer()
cli.add_typer(antigravity_app, name="antigravity")


def main() -> None:
    """Entry point (see [project.scripts] in pyproject.toml).

    Dispatches `antigravity render`/`title` to the stdlib-only fast path
    (see fast_antigravity_render/_title docstrings for the latency budget
    this exists to meet) before paying for typer/click's argument parsing
    and heavy imports. Assigning a monkeypatched `cli.__call__` here instead
    does NOT work: Python's implicit call syntax (`cli()`, which is exactly
    what a [project.scripts] entry point and `if __name__ == "__main__"` use)
    resolves special methods via `type(cli).__call__`, bypassing the
    instance's own `__dict__` entirely -- confirmed empirically, not just by
    the data model docs.
    """
    if len(sys.argv) >= 3 and sys.argv[1] == "antigravity":
        if sys.argv[2] == "render":
            fast_antigravity_render()
            return
        if sys.argv[2] == "title":
            fast_antigravity_title()
            return
    cli()


def fast_antigravity_render():
    """Fast-path stdlib renderer for Antigravity statusline.

    Antigravity CLI (agy) enforces a strict 1,000ms execution deadline on statusline commands.
    Exceeding this deadline causes agy to send SIGKILL to the process.
    To guarantee execution completes within ~20ms, this function bypasses heavy third-party
    imports (typer, pydantic, rich) and relies solely on Python stdlib json and ANSI formatting.
    """
    raw_data = {}
    if not sys.stdin.isatty():
        try:
            content = sys.stdin.read().strip()
            if content:
                raw_data = json.loads(content)
        except Exception:  # noqa: S110 -- malformed/partial stdin must render blank, not crash, within the 20ms budget
            pass

    state = raw_data.get("agent_state")
    model_raw = raw_data.get("model")
    model_data = model_raw if isinstance(model_raw, dict) else {}
    model_name = model_data.get("display_name")
    cwd = raw_data.get("cwd")
    vcs = raw_data.get("vcs") if isinstance(raw_data.get("vcs"), dict) else {}
    cw = raw_data.get("context_window") if isinstance(raw_data.get("context_window"), dict) else {}

    parts = []
    if state:
        colors = {
            "idle": "\033[2m",
            "thinking": "\033[36m",
            "working": "\033[34m",
            "tool_use": "\033[35m",
            "initializing": "\033[33m",
        }
        c = colors.get(state, "\033[37m")
        parts.append(f"{c}[{state}]\033[0m")
    if model_name:
        parts.append(f"\033[32m{model_name}\033[0m")
    if cwd:
        parts.append(f"\033[34m{Path(cwd).name}\033[0m")
    if vcs and vcs.get("branch"):
        branch = vcs["branch"]
        dirty = "*" if vcs.get("dirty") else ""
        parts.append(f"\033[33m{branch}{dirty}\033[0m")
    if cw and cw.get("used_percentage") is not None:
        pct = cw["used_percentage"]
        parts.append(f"\033[36m{pct:.1f}% context\033[0m")

    if parts:
        print("   ".join(parts))


def fast_antigravity_title():
    """Fast-path stdlib generator for Antigravity terminal titles.

    Executes within <10ms to satisfy Antigravity CLI's 1,000ms process deadline.
    """
    raw_data = {}
    if not sys.stdin.isatty():
        try:
            content = sys.stdin.read().strip()
            if content:
                raw_data = json.loads(content)
        except Exception:  # noqa: S110 -- malformed/partial stdin must render blank, not crash, within the 10ms budget
            pass

    cwd = raw_data.get("cwd")
    basename = Path(cwd).name if cwd else None
    model_raw = raw_data.get("model")
    model_data = model_raw if isinstance(model_raw, dict) else {}
    display_name = model_data.get("display_name")
    conv_id = raw_data.get("conversation_id")
    short_id = conv_id.split("-")[0] if conv_id else None
    state = raw_data.get("agent_state")

    candidates = [
        f"[{state}]" if state else None,
        basename,
        f"({display_name})" if display_name else None,
        f"- {short_id}" if short_id else None,
    ]
    parts = [part for part in candidates if part]
    title = " ".join(parts) if parts else "Antigravity"
    print(title)


@antigravity_app.command("render")
def antigravity_render():
    fast_antigravity_render()


@antigravity_app.command("title")
def antigravity_title():
    fast_antigravity_title()


def _parse_segment_result(data: Any) -> list[SegmentGenerationResult]:
    items = data if isinstance(data, list) else [data]
    results = []
    for item in items:
        if isinstance(item, dict) and "segment" in item and isinstance(item["segment"], dict):
            seg = Segment(text=item["segment"].get("text", ""))
            results.append(
                SegmentGenerationResult(
                    segment=seg,
                    line=item.get("line", 0),
                    index=item.get("index", 0),
                    column=item.get("column"),
                    generator=item.get("generator", "internal"),
                    cache_duration=item.get("cache_duration"),
                )
            )
    return results


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
                parsed = json.loads(stdout)
                results = _parse_segment_result(parsed)

                for item in results:
                    item.generator = cmd
                return results
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
        payload = StatusLineStdIn.from_dict(raw_data)
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
        ]
        for result_list in internal_results_nested:
            all_segments = all_segments + result_list
    except Exception as e:
        all_segments = all_segments + handle_error(e, "internal.claude_or_workspace")

    lines = render_lines(payload, None, all_segments, terminal_width=terminal_width)

    for line in lines:
        print(line)


dev_app = typer.Typer()
cli.add_typer(dev_app, name="dev")


def _mock_payload(cost_usd: float = 42.50, duration_ms: int = 3_723_000, used_pct: float = 47.0) -> StatusLineStdIn:
    return StatusLineStdIn(
        model=ModelInfo(display_name="Sonnet 5"),
        cost=CostInfo(total_cost_usd=cost_usd, total_duration_ms=duration_ms),
        context_window=ContextWindowInfo(
            total_input_tokens=int(1_000_000 * used_pct / 100),
            context_window_size=1_000_000,
            used_percentage=used_pct,
        ),
        output_style=OutputStyle(name="concise"),
    )


def _mock_git_info(branch: str = "main", **overrides) -> GitInfo:
    info = GitInfo(
        branch=branch,
        remote="https://github.com/example/repo",
        dirty=False,
        staged=False,
        untracked=False,
        ahead=0,
        behind=0,
        is_repo=True,
        stash_count=0,
    )
    return replace(info, **overrides) if overrides else info


def _build_scenario(name: str) -> list[SegmentGenerationResult]:
    payload = _mock_payload()
    common = [
        *format_model_info(payload),
        *format_directory(Path("/Users/example/project")),
        *format_session_info(payload),
        *format_cost(payload),
        *format_context_usage(payload.context_window),
    ]

    if name == "single-repo":
        return [*common, *_format_repo("", _mock_git_info(), line=2)]

    if name == "dual-repo":
        overlay = _mock_git_info("main", ahead=1)
        base = _mock_git_info("feature/dashboard", dirty=True, staged=True)
        return [*common, *_format_repo("overlay", overlay, line=2), *_format_repo("base", base, line=3)]

    if name == "long-branch":
        overlay = _mock_git_info("main")
        base = _mock_git_info("feature/a-very-long-branch-name-that-needs-truncating", dirty=True)
        return [*common, *_format_repo("overlay", overlay, line=2), *_format_repo("base", base, line=3)]

    if name == "dirty":
        info = _mock_git_info("main", dirty=True, staged=True, untracked=True, ahead=3, behind=1, stash_count=2)
        return [*common, *_format_repo("", info, line=2)]

    raise typer.BadParameter(f"Unknown scenario {name!r}. Choices: single-repo, dual-repo, long-branch, dirty")


@dev_app.command("preview")
def dev_preview(
    scenario: Annotated[str, typer.Argument(help="single-repo | dual-repo | long-branch | dirty")],
    width: Annotated[int | None, typer.Option(help="Force a terminal width instead of probing it.")] = None,
    image: Annotated[
        bool, typer.Option("--image", help="Also render a PNG (via qlmanage) and print its path.")
    ] = False,
) -> None:
    """Render a canonical mock scenario directly -- no live git calls, no Claude Code
    session needed. Point of this command: iterating on rendering shouldn't require
    hand-writing a JSON payload and a subprocess pipeline every time.
    """
    segments = _build_scenario(scenario)
    lines = render_lines(None, None, segments, terminal_width=width)
    for line in lines:
        print(line)

    if not image:
        return

    with Path(os.devnull).open("w") as devnull:
        console = Console(record=True, color_system="truecolor", width=width or 120, file=devnull)
        for line in lines:
            console.print(Text.from_ansi(line, no_wrap=True))

    svg_path = Path(tempfile.gettempdir()) / f"termstatus-preview-{scenario}.svg"
    console.save_svg(str(svg_path), title=f"preview: {scenario}")

    result = subprocess.run(
        ["qlmanage", "-t", "-s", "1200", "-o", str(svg_path.parent), str(svg_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    png_path = svg_path.with_suffix(".svg.png")
    if result.returncode == 0 and png_path.exists():
        print(f"image: {png_path}")
    else:
        print(f"qlmanage failed (macOS QuickLook only): {result.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    main()
