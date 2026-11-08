import io
import json
import sys
from collections.abc import Mapping, MutableMapping
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from whenever import TimeDelta

from termstatus.agy.cli import render_from_stdin
from termstatus.agy.git import fallback_vcs, resolve_vcs
from termstatus.agy.protocol import Quota, decode_payload
from termstatus.agy.statusline import (
    _format_quota_label,
    _format_quota_reset_duration,
    _thinking_cellular_graph,
    display_width,
    git_branch,
    render_statusline,
    strip_ansi,
)
from termstatus.agy.term_colors import fullness_icon, meter_color
from termstatus.git_status import VcsState, parse_git_status
from termstatus.main import main
from termstatus.segments.constants import CYAN, DIM, GREEN, ORANGE, RED, YELLOW

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


def rendered(raw: Mapping[str, object], vcs: VcsState | None = None) -> list[str]:
    return strip_ansi(render_statusline(decode_payload(raw), vcs)).splitlines()


def test_wide_render_uses_five_conditional_rows() -> None:
    lines = rendered(FULL_PAYLOAD)

    assert len(lines) == 5
    assert all(
        expected in line
        for expected, line in zip(
            (
                "working",
                "GPT-5.6",
                "think:high",
                "autonomous",
                "plan:full",
                "sandbox:no-net",
                "vim:insert",
            ),
            [lines[0]] * 7,
            strict=True,
        )
    )
    assert " • " in lines[0]
    assert "/work/repo" in lines[1]
    assert "82% ctx" in lines[1]
    assert "5h ◕ 50%" in lines[1]
    assert "$0.01" in lines[1]
    assert " • " in lines[1]
    assert "7d ◔ 10%" in lines[2]
    assert "5h" not in lines[2]
    assert "<feature/renderer → origin/feature/renderer>" in lines[3]
    assert "!" in lines[3]
    assert "↑2" in lines[3] and "↓1" in lines[3]
    assert "tasks:3" in lines[4] and "input:2" in lines[4]
    assert "confirm" in lines[4] and "artifacts:1" in lines[4]
    assert " • " in lines[4]


def test_quota_row_layout_and_bracket_formatting() -> None:
    payload = {
        "cwd": "/work/repo",
        "quota": {
            "gemini-5h": {"remaining_percentage": 81, "reset_in_seconds": 1800},
            "gemini-weekly": {"remaining_percentage": 10, "reset_in_seconds": 7200},
        },
        "terminal_width": 160,
    }
    with patch(
        "termstatus.agy.statusline._format_quota_reset_duration",
        side_effect=lambda delta: "⏳ 30m" if delta and delta.total("seconds") == 1800 else "⏳ 2h",
    ):
        lines = rendered(payload)

    assert len(lines) == 3
    assert "/work/repo" in lines[1]
    assert "[5h ● 81% ⏳ 30m]" in lines[1]
    assert " • " in lines[1]
    assert "[7d ◔ 10% ⏳ 2h]" in lines[2]

    solo_payload = {
        "cwd": "/work/repo",
        "quota": {
            "gemini-5h": {"remaining_percentage": 81, "reset_in_seconds": 1800},
        },
        "terminal_width": 160,
    }
    with patch("termstatus.agy.statusline._format_quota_reset_duration", return_value="⏳ 30m"):
        solo_lines = rendered(solo_payload)

    assert len(solo_lines) == 2
    assert "/work/repo • [5h ● 81% ⏳ 30m]" in solo_lines[1]


def test_narrow_render_omits_lower_priority_slots_without_overflowing() -> None:
    lines = rendered({**FULL_PAYLOAD, "terminal_width": 40})

    assert "working" in lines[0]
    assert "plan:full" not in lines[0] and "vim:insert" not in lines[0]
    assert all(display_width(line) <= 40 for line in lines)


def test_payload_display_text_cannot_inject_terminal_controls_or_rows() -> None:
    output = render_statusline(
        decode_payload(
            {
                "agent_state": "working\x1b[41m",
                "cwd": "/work\nrepo",
                "model": {"display_name": "model\x1b]8;;bad\x1b\\"},
                "quota": {"quota\nname\x1b[41m": {"remaining_percentage": 50}},
                "terminal_width": 160,
            }
        ),
        VcsState("branch\nname\x1b[41m", True, True),
    )

    assert output.count("\n") == 3
    assert "\x1b[41m" not in output
    assert "\r" not in output


def test_disabled_sandbox_is_hidden() -> None:
    assert "sandbox:off" not in "\n".join(rendered({"sandbox": {"enabled": False}, "terminal_width": 160}))


def test_enabled_sandbox_is_rendered() -> None:
    assert "sandbox:net" in "\n".join(
        rendered({"sandbox": {"enabled": True, "allow_network": True}, "terminal_width": 160})
    )
    assert "sandbox:no-net" in "\n".join(
        rendered({"sandbox": {"enabled": True, "allow_network": False}, "terminal_width": 160})
    )


@pytest.mark.parametrize(
    ("dirty", "untracked", "flag"),
    [(True, False, "[!]"), (False, True, "[?]"), (False, False, "[✓]")],
)
def test_detached_repository_shows_detached_state_with_status_flag(dirty: bool, untracked: bool, flag: str) -> None:
    line = render_statusline(
        decode_payload({"terminal_width": 80}),
        VcsState(None, dirty, True, untracked=untracked, commit="113285f1a6ea58a80bde1e59f5d626779fd6180a"),
    )

    stripped = strip_ansi(line)
    assert "(detached@113285f)" in stripped
    assert flag in stripped
    assert "dirty" not in stripped


def test_quota_without_reset_is_rendered() -> None:
    assert "quota ◕ 50%" in "\n".join(rendered({"quota": {"quota": {"remaining_percentage": 50}}}))


def test_decoded_quotas_are_immutable_and_use_time_delta_resets() -> None:
    quota = decode_payload({"quota": {"five-hour": {"remaining_percentage": 50, "reset_in_seconds": 1800}}}).quotas[
        "five-hour"
    ]

    assert quota == Quota(remaining=50, reset_in=TimeDelta(minutes=30))
    with pytest.raises(TypeError):
        cast(MutableMapping[str, Quota], decode_payload({}).quotas)["new"] = quota
    with pytest.raises(FrozenInstanceError):
        field = "remaining"
        setattr(quota, field, 0)


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


def test_state_icon_inside_brackets() -> None:
    lines = rendered({"agent_state": "working"})
    assert "[🔄 working]" in lines[0]

    thinking = rendered({"agent_state": "thinking"})
    assert "[🧠 thinking]" in thinking[0]


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


def test_main_dispatches_antigravity_render_without_subprocess(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["statusline", "antigravity", "render"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    with patch("termstatus.git_status.asyncio.create_subprocess_exec") as create_process:
        main()

    assert strip_ansi(capsys.readouterr().out) == "[idle]\n"
    create_process.assert_not_called()


def test_huge_valid_json_numbers_render_without_throwing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    huge = 10**1000
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "terminal_width": huge,
                    "context_window": {"remaining_percentage": huge},
                    "quota": {"quota": {"remaining_percentage": huge}},
                }
            )
        ),
    )

    render_from_stdin()

    assert "[idle]" in strip_ansi(capsys.readouterr().out)


def test_resolution_error_uses_payload_branch_and_dirty_fallback_only(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO('{"cwd":"/work/repo","vcs":{"branch":"payload","dirty":true,"upstream":"stale","ahead":2}}'),
    )
    with patch("termstatus.agy.cli.resolve_vcs", new=AsyncMock(side_effect=RuntimeError)):
        render_from_stdin()

    output = strip_ansi(capsys.readouterr().out)
    assert "payload" in output
    assert "\uf06a" in output or "!" in output
    assert "stale" not in output and "ahead:2" not in output


def test_parse_porcelain_v2_and_renders_github_origin_as_osc8_link() -> None:
    vcs = parse_git_status(
        b"# branch.oid abc123\n# branch.head feature/demo\n# branch.upstream origin/feature/demo\n# branch.ab +2 -1\n1 .M N... 100644 100644 100644 abc abc file.py\n"
    )

    assert vcs == VcsState("feature/demo", True, True, "origin/feature/demo", 2, 1, commit="abc123")
    line = render_statusline(
        decode_payload({"terminal_width": 160}),
        VcsState("feature/demo", False, True, "origin/feature/demo", 2, 1, "git@github.com:stripe/example.git"),
    )
    assert "\033]8;;https://github.com/stripe/example\033\\feature/demo\033]8;;\033\\" in line


def test_parse_porcelain_v2_detached_head_extracts_commit_and_renders_link() -> None:
    vcs = parse_git_status(b"# branch.oid 113285f1a6ea58a80bde1e59f5d626779fd6180a\n# branch.head (detached)\n")

    assert vcs == VcsState(None, False, True, commit="113285f1a6ea58a80bde1e59f5d626779fd6180a")
    line = render_statusline(
        decode_payload({"terminal_width": 160}),
        VcsState(
            None,
            False,
            True,
            origin_url="git@github.com:stripe/example.git",
            commit="113285f1a6ea58a80bde1e59f5d626779fd6180a",
        ),
    )
    assert (
        "\033]8;;https://github.com/stripe/example/commit/113285f1a6ea58a80bde1e59f5d626779fd6180a\033\\113285f\033]8;;\033\\"
        in line
    )
    assert "(detached@" in line
    assert "[✓]" in strip_ansi(line)


def test_fallback_vcs_preserves_untracked_state() -> None:
    payload = decode_payload({"vcs": {"branch": "feature/fallback", "dirty": False, "untracked": True}})
    vcs = fallback_vcs(payload)
    assert vcs is not None
    assert vcs.untracked is True


def test_osc8_git_branch_uses_only_visible_width_when_fitting_slots() -> None:
    vcs = VcsState("界界", False, True, origin_url="git@github.com:stripe/example.git")

    assert display_width(git_branch(vcs) or "") == 10
    assert "界界" in render_statusline(decode_payload({"terminal_width": 10}), vcs)


def test_branch_status_icons() -> None:
    clean = git_branch(VcsState("main", False, True))
    assert clean is not None
    assert "\x1b[35m" in clean  # Magenta branch
    assert "\x1b[32m" in clean  # Green clean icon
    assert "✓" in clean
    assert "[" in clean and "]" in clean

    dirty = git_branch(VcsState("main", True, True))
    assert dirty is not None
    assert "\x1b[35m" in dirty  # Magenta branch
    assert "\x1b[33m" in dirty  # Yellow dirty icon
    assert "!" in dirty
    assert "[" in dirty and "]" in dirty

    complex_vcs = git_branch(VcsState("feature", True, True, ahead=3, behind=1, rebase=True, untracked=True))
    assert complex_vcs is not None
    assert "REBASE" in complex_vcs
    assert "!" in complex_vcs
    assert "?" in complex_vcs
    assert "[! ?]" in strip_ansi(git_branch(VcsState("both", True, True, untracked=True)) or "")
    assert "↑3" in complex_vcs
    assert "↓1" in complex_vcs


def test_branch_pairing_format() -> None:
    paired = git_branch(VcsState("main", False, True, upstream="origin/main"))
    assert paired is not None
    assert "<main → origin/main>" in strip_ansi(paired)
    assert "\x1b[35m" in paired  # Magenta local branch
    assert "\x1b[36m" in paired  # Cyan remote branch
    assert "[✓]" in strip_ansi(paired)

    unpaired = git_branch(VcsState("feature/local", True, True))
    assert unpaired is not None
    assert "<" not in strip_ansi(unpaired) and "→" not in strip_ansi(unpaired)
    assert "feature/local [!]" in strip_ansi(unpaired)


def test_3p_quotas_filtered_and_quota_meters_formatted() -> None:
    lines = rendered(
        {
            "quota": {
                "3p-5h": {"remaining_percentage": 100},
                "3p-weekly": {"remaining_percentage": 100},
                "gemini-5h": {"remaining_percentage": 97},
                "gemini-weekly": {"remaining_percentage": 84},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "3p-5h" not in plain
    assert "3p-weekly" not in plain
    assert "capacity:" not in plain
    assert "[5h ● 97%]" in lines[1]
    assert "[7d ● 84%]" in lines[2]


def test_format_quota_label_preserves_tier_and_normalizes_intervals() -> None:
    assert _format_quota_label("gemini-pro-weekly") == "pro-7d"
    assert _format_quota_label("pro-weekly") == "pro-7d"
    assert _format_quota_label("gemini-5h") == "5h"
    assert _format_quota_label("gemini-weekly") == "7d"
    assert _format_quota_label("codex-5h") == "5h"
    assert _format_quota_label("codex-weekly") == "7d"
    assert _format_quota_label("pro-5h") == "pro-5h"
    assert _format_quota_label("gemini-pro-5h") == "pro-5h"
    assert _format_quota_label("3p-5h") is None
    assert _format_quota_label("3p_weekly") is None
    assert _format_quota_label("3p:daily") is None
    assert _format_quota_label("user-limit") == "limit"
    assert _format_quota_label("quota") == "quota"


def test_format_quota_reset_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _format_quota_reset_duration(None) is None
    assert _format_quota_reset_duration(TimeDelta(seconds=0)) is None
    assert _format_quota_reset_duration(TimeDelta(seconds=-1)) is None

    assert (
        strip_ansi(_format_quota_reset_duration(TimeDelta(days=5, hours=6, minutes=12, days_assumed_24h_ok=True)) or "")
        == "⏳ 5d 6h 12m"
    )
    assert strip_ansi(_format_quota_reset_duration(TimeDelta(hours=2, minutes=15)) or "") == "⏳ 2h 15m"
    assert strip_ansi(_format_quota_reset_duration(TimeDelta(minutes=45)) or "") == "⏳ 45m"
    assert strip_ansi(_format_quota_reset_duration(TimeDelta(seconds=30)) or "") == "⏳ 1m"

    monkeypatch.setenv("TERMSTATUS_NO_ICONS", "1")
    assert strip_ansi(_format_quota_reset_duration(TimeDelta(hours=2, minutes=15)) or "") == "2h 15m"
    monkeypatch.delenv("TERMSTATUS_NO_ICONS", raising=False)

    short_reset = _format_quota_reset_duration(TimeDelta(seconds=1800))
    assert short_reset is not None
    assert CYAN in short_reset

    long_reset = _format_quota_reset_duration(TimeDelta(seconds=1801))
    assert long_reset is not None
    assert DIM in long_reset


def test_quota_labels_disambiguate_multiple_buckets_sharing_interval() -> None:
    lines = rendered(
        {
            "quota": {
                "gemini-weekly": {"remaining_percentage": 80},
                "gemini-pro-weekly": {"remaining_percentage": 50},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "[gemini-7d" in plain
    assert "[pro-7d" in plain
    assert "[7d " not in plain

    lines = rendered(
        {
            "quota": {
                "gemini-weekly": {"remaining_percentage": 80},
                "pro-weekly": {"remaining_percentage": 50},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "[gemini-7d" in plain
    assert "[pro-7d" in plain

    lines = rendered(
        {
            "quota": {
                "gemini-weekly": {"remaining_percentage": 80},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "[7d " in plain
    assert "[gemini-7d" not in plain

    lines = rendered(
        {
            "quota": {
                "gemini-5h": {"remaining_percentage": 80},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "[5h " in plain
    assert "[gemini-5h" not in plain

    lines = rendered(
        {
            "quota": {
                "gemini-5h": {"remaining_percentage": 80},
                "gemini-pro-5h": {"remaining_percentage": 50},
            },
            "terminal_width": 160,
        }
    )
    plain = "\n".join(lines)
    assert "[gemini-5h" in plain
    assert "[pro-5h" in plain


def test_model_name_strips_effort_case_insensitively() -> None:
    lines = rendered(
        {
            "model": {"display_name": "Gemini 3.8 Flash (Medium)"},
            "effort": "medium",
            "terminal_width": 160,
        }
    )
    assert "Gemini 3.8 Flash" in lines[0]
    assert "think:medium" in lines[0]
    assert "Gemini 3.8 Flash (Medium)" not in lines[0]


def test_directory_shortening_and_link() -> None:
    home = str(Path.home())
    lines = rendered({"cwd": f"{home}/.local/share/chezmoi", "terminal_width": 160})
    assert "~/.local/share/chezmoi" in lines[1]


def test_fullness_icon() -> None:
    assert fullness_icon(100) == "●"
    assert fullness_icon(78) == "●"
    assert fullness_icon(75) == "●"
    assert fullness_icon(70) == "◕"
    assert fullness_icon(50) == "◕"
    assert fullness_icon(45) == "◑"
    assert fullness_icon(25) == "◑"
    assert fullness_icon(18) == "◔"
    assert fullness_icon(5) == "◔"
    assert fullness_icon(4) == "○"
    assert fullness_icon(0) == "○"


def test_meter_color_tiers() -> None:
    assert meter_color(95) == GREEN
    assert meter_color(78) == GREEN
    assert meter_color(70) == GREEN
    assert meter_color(60) == YELLOW
    assert meter_color(40) == YELLOW
    assert meter_color(30) == ORANGE
    assert meter_color(18) == ORANGE
    assert meter_color(15) == ORANGE
    assert meter_color(14) == RED
    assert meter_color(10) == RED
    assert meter_color(0) == RED


def test_thinking_cellular_graph() -> None:
    assert strip_ansi(_thinking_cellular_graph("low")) == "▂▅█"
    assert strip_ansi(_thinking_cellular_graph("medium")) == "▂▅█"
    assert strip_ansi(_thinking_cellular_graph("high")) == "▂▅█"
    assert strip_ansi(_thinking_cellular_graph("off")) == "▂▅█"

    # Off: all 3 bars in dark grey, no cyan
    off = _thinking_cellular_graph("off")
    assert "\x1b[36m" not in off
    assert "\x1b[90m" in off

    # Low: 1st bar cyan, remaining dark grey
    low = _thinking_cellular_graph("low")
    assert low.count("\x1b[36m") == 1
    assert low.count("\x1b[90m") == 2

    # Medium: 2 bars cyan, 1 dark grey
    med = _thinking_cellular_graph("medium")
    assert med.count("\x1b[36m") == 2
    assert med.count("\x1b[90m") == 1

    # High: all 3 cyan, no dark grey
    high = _thinking_cellular_graph("high")
    assert high.count("\x1b[36m") == 3
    assert "\x1b[90m" not in high

    assert _thinking_cellular_graph(None) == ""
    assert _thinking_cellular_graph("unknown") == ""


def test_resilience_against_malformed_and_extreme_inputs() -> None:
    for bad in (float("nan"), float("inf"), float("-inf")):
        assert meter_color(bad) is not None
        assert fullness_icon(bad) is not None

    raw = {
        "cwd": "///invalid/path/\\//",
        "context_window": {"remaining_percentage": -50},
        "cost": {"estimated": float("inf")},
        "terminal_width": -1,
        "quota": {"": {"remaining_percentage": 999}},
    }
    output = render_statusline(decode_payload(raw), VcsState(None, False, False))
    assert isinstance(output, str)


@pytest.mark.asyncio
async def test_git_probe_is_not_started_without_a_cwd() -> None:
    with patch("termstatus.git_status.asyncio.create_subprocess_exec") as create_process:
        assert await resolve_vcs(decode_payload({"vcs": {"branch": "payload", "dirty": True}})) == VcsState(
            "payload", True, True
        )

    create_process.assert_not_called()
