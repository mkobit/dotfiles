import asyncio
import io
import sys
import time
from unittest.mock import patch

import pytest

from termstatus.agy import (
    VcsState,
    decode_payload,
    display_width,
    git_branch,
    parse_git_status,
    probe_git,
    render_from_stdin,
    render_statusline,
    resolve_vcs,
    strip_ansi,
)

FULL_PAYLOAD = {
    "agent_state": "working",
    "cwd": "/work/repo",
    "model": {"display_name": "GPT-5.6 (high)", "effort": "high"},
    "execution_mode": "autonomous",
    "plan": {"tier": "full"},
    "sandbox": {"enabled": True, "allow_network": False},
    "vim_mode": "insert",
    "context_window": {"remaining_percentage": 82},
    "quota": {
        "codex-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 1800},
        "codex-weekly": {"remaining_percentage": 10, "reset_in_seconds": 7200},
    },
    "cost": {"estimated": 0.01},
    "vcs": {
        "branch": "feature/renderer",
        "dirty": True,
        "upstream": "origin/feature/renderer",
        "ahead": 2,
        "behind": 1,
    },
    "tasks": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
    "pending_input_count": 2,
    "confirmation_pending": True,
    "artifacts": [{"id": "one"}],
    "terminal_width": 160,
}


def rendered(raw: dict[str, object], vcs: VcsState | None = None) -> list[str]:
    return strip_ansi(render_statusline(decode_payload(raw), vcs)).splitlines()


def test_wide_render_uses_four_conditional_rows() -> None:
    lines = rendered(FULL_PAYLOAD)

    assert len(lines) == 4
    assert all(
        expected in line
        for expected, line in zip(
            (
                "working",
                "GPT-5.6",
                "high",
                "autonomous",
                "plan:full",
                "sandbox:no-net",
                "vim:insert",
            ),
            [lines[0]] * 7,
            strict=True,
        )
    )
    assert "/work/repo" in lines[1]
    assert "82% ctx" in lines[1] and "codex-5h:50%" in lines[1] and "codex-weekly:10%" in lines[1]
    assert "$0.01" in lines[1]
    assert "feature/renderer*" in lines[2] and "origin/feature/renderer" in lines[2]
    assert "ahead:2" in lines[2] and "behind:1" in lines[2]
    assert "tasks:3" in lines[3] and "input:2" in lines[3]
    assert "confirm" in lines[3] and "artifacts:1" in lines[3]


def test_narrow_render_omits_lower_priority_slots_without_overflowing() -> None:
    lines = rendered({**FULL_PAYLOAD, "terminal_width": 40})

    assert "working" in lines[0]
    assert "plan:full" not in lines[0] and "vim:insert" not in lines[0]
    assert all(display_width(line) <= 40 for line in lines)


def test_missing_optional_fields_omit_empty_rows_and_sensitive_fields() -> None:
    lines = rendered(
        {
            "agent_state": "idle",
            "email": "person@example.com",
            "transcript_path": "/private/transcript",
            "product": "antigravity",
            "version": "9.9.9",
        }
    )

    assert lines == ["[idle]"]
    assert "person@example.com" not in "\n".join(lines)


def test_reasoning_precedence_is_model_effort_then_reasoning_then_top_level() -> None:
    assert decode_payload({"model": {"effort": "high", "reasoning_effort": "medium"}, "effort": "low"}).effort == "high"
    assert decode_payload({"model": {"reasoning_effort": "medium"}, "effort": "low"}).effort == "medium"
    assert decode_payload({"effort": "low"}).effort == "low"


def test_activity_task_count_never_invents_a_total() -> None:
    line = "\n".join(rendered({"tasks": 3, "terminal_width": 80}))

    assert "tasks:3" in line
    assert "/" not in line


def test_malformed_json_renders_without_throwing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    render_from_stdin()

    assert strip_ansi(capsys.readouterr().out) == "[idle]\n"


def test_parse_porcelain_v2_and_renders_github_origin_as_osc8_link() -> None:
    vcs = parse_git_status(
        b"# branch.oid abc123\n# branch.head feature/demo\n# branch.upstream origin/feature/demo\n# branch.ab +2 -1\n1 .M N... 100644 100644 100644 abc abc file.py\n"
    )

    assert vcs == VcsState("feature/demo", True, True, "origin/feature/demo", 2, 1)
    line = render_statusline(
        decode_payload({"terminal_width": 160}),
        VcsState("feature/demo", False, True, "origin/feature/demo", 2, 1, "git@github.com:stripe/example.git"),
    )
    assert "\033]8;;https://github.com/stripe/example\033\\feature/demo\033]8;;\033\\" in line


def test_osc8_git_branch_uses_only_visible_width_when_fitting_slots() -> None:
    vcs = VcsState("界界", False, True, origin_url="git@github.com:stripe/example.git")

    assert display_width(git_branch(vcs) or "") == 4
    assert "界界" in render_statusline(decode_payload({"terminal_width": 10}), vcs)


@pytest.mark.asyncio
async def test_git_probe_launches_exactly_two_commands_and_falls_back_after_shared_deadline() -> None:
    async def slow_start(*_args: object, **_kwargs: object) -> object:
        await asyncio.sleep(1)
        raise AssertionError("unreachable")

    started = time.perf_counter()
    with patch("termstatus.agy.asyncio.create_subprocess_exec", side_effect=slow_start) as create_process:
        payload = decode_payload(
            {
                "cwd": "/work/repo",
                "vcs": {"branch": "payload", "dirty": True, "upstream": "stale", "ahead": 2, "behind": 1},
            }
        )
        assert await resolve_vcs(payload) == VcsState("payload", True, True)

    assert time.perf_counter() - started < 0.2
    assert create_process.await_count == 2


@pytest.mark.asyncio
async def test_git_probe_cancels_communicates_and_reaps_processes_within_deadline() -> None:
    class SlowProcess:
        def __init__(self) -> None:
            self.returncode: int | None = None
            self.killed = False
            self.communicate_cancelled = False
            self.wait_started = False

        async def communicate(self) -> tuple[bytes, bytes]:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.communicate_cancelled = True
                raise
            return b"", b""

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> int:
            self.wait_started = True
            await asyncio.Event().wait()
            return 0

    processes = [SlowProcess(), SlowProcess()]
    launches = processes.copy()

    async def start(*_args: object, **_kwargs: object) -> SlowProcess:
        return launches.pop(0)

    started = time.perf_counter()
    with patch("termstatus.agy.asyncio.create_subprocess_exec", side_effect=start) as create_process:
        assert await probe_git("/work/repo") is None

    assert time.perf_counter() - started < 0.2
    assert create_process.await_count == 2
    assert all(process.killed and process.communicate_cancelled and process.wait_started for process in processes)


@pytest.mark.asyncio
async def test_git_probe_is_not_started_without_a_cwd() -> None:
    with patch("termstatus.agy.asyncio.create_subprocess_exec") as create_process:
        assert await resolve_vcs(decode_payload({"vcs": {"branch": "payload", "dirty": True}})) == VcsState(
            "payload", True, True
        )

    create_process.assert_not_called()
