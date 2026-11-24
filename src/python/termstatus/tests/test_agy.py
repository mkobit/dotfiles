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
from termstatus.segments.constants import CYAN, DIM, GREEN, MAGENTA, ORANGE, RED, YELLOW

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


def test_wide_render_uses_four_aligned_table_rows() -> None:
    lines = rendered(FULL_PAYLOAD)

    assert len(lines) == 4
    assert all(" • " not in line for line in lines)
    assert all(
        expected in lines[0]
        for expected in (
            "[🔄 working] \ue7c5I",
            "GPT-5.6",
            "high",
            "autonomous",
            "sandbox:no-net",
        )
    )
    assert "think:" not in lines[0]
    assert "vim:" not in lines[0]
    assert "plan:" not in lines[0]
    assert "full" not in lines[0]
    assert "/work/repo" in lines[1]
    assert "<feature/renderer → origin/feature/renderer>" in lines[1]
    assert "!" in lines[1]
    assert "↑2" in lines[1] and "↓1" in lines[1]

    assert "82% ctx" in lines[2]
    assert "5h ◕ 50%" in lines[2]
    assert "7d ◔ 10%" in lines[2]
    assert lines[2].index("5h ◕ 50%") < lines[2].index("7d ◔ 10%")
    assert "$0.01" in lines[2]
    assert "full" in lines[2]
    assert "plan:" not in lines[2]
    assert lines[2].index("$0.01") < lines[2].index("full")

    assert lines[3].startswith("confirm")
    assert "tasks:3" in lines[3] and "input:2" in lines[3] and "artifacts:1" in lines[3]

    # Verify Col 1 aligns vertically across all 4 rows
    col1_starts = [
        display_width(lines[0][: lines[0].index("GPT-5.6")]),
        display_width(lines[1][: lines[1].index("<feature/renderer") - 2]),
        display_width(lines[2][: lines[2].index("[5h")]),
        display_width(lines[3][: lines[3].index("tasks:3")]),
    ]
    assert len(set(col1_starts)) == 1

    # Verify Col 2 aligns vertically between Row 0 and Row 2
    col2_starts = [
        display_width(lines[0][: lines[0].index("autonomous")]),
        display_width(lines[2][: lines[2].index("$0.01")]),
    ]
    assert len(set(col2_starts)) == 1


@pytest.mark.parametrize("width", [40, 60, 80, 120, 160])
def test_responsive_table_never_exceeds_terminal_width(width: int) -> None:
    lines = rendered({**FULL_PAYLOAD, "terminal_width": width})

    assert len(lines) >= 1
    assert "working" in lines[0]
    assert all(display_width(line) <= width for line in lines)


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
    assert "[5h ● 81% ⏳ 30m]  [7d ◔ 10% ⏳ 2h]" in lines[2]

    solo_payload = {
        "cwd": "/work/repo",
        "quota": {
            "gemini-5h": {"remaining_percentage": 81, "reset_in_seconds": 1800},
        },
        "terminal_width": 160,
    }
    with patch("termstatus.agy.statusline._format_quota_reset_duration", return_value="⏳ 30m"):
        solo_lines = rendered(solo_payload)

    assert len(solo_lines) == 3
    assert "/work/repo" in solo_lines[1]
    assert "[5h ● 81% ⏳ 30m]" in solo_lines[2]


def test_narrow_render_omits_lower_priority_slots_and_splits_overflow_quotas() -> None:
    lines = rendered({**FULL_PAYLOAD, "terminal_width": 40})

    assert "[🔄 working] \ue7c5I" in lines[0]
    assert "GPT-5.6" in lines[0]
    assert "autonomous" not in lines[0] and "sandbox:no-net" not in lines[0]
    assert all(display_width(line) <= 40 for line in lines)
    plain = "\n".join(lines)
    assert "5h ◕ 50%" in plain
    assert "7d ◔ 10%" in plain
    # 7d quota splits onto a continuation usage row at width 40
    usage_idx = next(idx for idx, line in enumerate(lines) if "82% ctx" in line)
    assert "5h ◕ 50%" in lines[usage_idx]
    assert "7d ◔ 10%" in lines[usage_idx + 1]
    assert "full" not in lines[usage_idx]


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

    assert output.count("\n") == 2
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


def test_live_agy_payload_field_aliases() -> None:
    payload = decode_payload(
        {
            "cycle_mode": "accept-edits",
            "vim": {"mode": "INSERT"},
            "tool_confirmation_pending": True,
        }
    )
    assert payload.execution_mode == "accept-edits"
    assert payload.vim_mode == "INSERT"
    assert payload.confirmation_pending is True

    # Precedence checks
    assert (
        decode_payload({"execution_mode": "auto", "cycle_mode": "accept-edits", "mode": "ask"}).execution_mode == "auto"
    )
    assert decode_payload({"cycle_mode": "accept-edits", "mode": "ask"}).execution_mode == "accept-edits"
    assert decode_payload({"mode": "ask"}).execution_mode == "ask"
    assert decode_payload({"vim_mode": "normal", "vim": {"mode": "INSERT"}}).vim_mode == "normal"
    assert (
        decode_payload({"confirmation_pending": False, "tool_confirmation_pending": True}).confirmation_pending is False
    )
    assert (
        decode_payload({"tool_confirmation_pending": False, "confirmation": {"pending": True}}).confirmation_pending
        is False
    )
    assert decode_payload({"confirmation": {"pending": True}}).confirmation_pending is True


def test_activity_task_count_never_invents_a_total() -> None:
    line = "\n".join(rendered({"tasks": 3, "terminal_width": 80}))

    assert "tasks:3" in line
    assert "/" not in line


def test_malformed_json_renders_visible_error_token(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TERMSTATUS_DEBUG", raising=False)
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    render_from_stdin()

    captured = capsys.readouterr()
    assert strip_ansi(captured.out) == "[statusline:err]\n"
    assert RED in captured.out
    assert captured.err == ""


def test_malformed_json_prints_traceback_when_debug_enabled(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TERMSTATUS_DEBUG", "1")
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    render_from_stdin()

    captured = capsys.readouterr()
    assert strip_ansi(captured.out) == "[statusline:err]\n"
    assert "JSONDecodeError" in captured.err


def test_main_dispatches_antigravity_render_without_subprocess(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["statusline", "antigravity", "render"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    with patch("termstatus.git_status.asyncio.create_subprocess_exec") as create_process:
        main()

    assert strip_ansi(capsys.readouterr().out) == "[statusline:err]\n"
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
    assert "[7d ● 84%]" in lines[1]


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


def test_model_name_strips_effort_case_insensitively(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = rendered(
        {
            "model": {"display_name": "Gemini 3.8 Flash (Medium)"},
            "effort": "medium",
            "terminal_width": 160,
        }
    )
    assert "Gemini 3.8 Flash" in lines[0]
    assert "🧠 ▁▂▄▆█ medium" in lines[0]
    assert "think:" not in lines[0]
    assert "Gemini 3.8 Flash (Medium)" not in lines[0]

    monkeypatch.setenv("TERMSTATUS_NO_ICONS", "1")
    no_icon_lines = rendered(
        {
            "model": {"display_name": "Gemini 3.8 Flash (Medium)"},
            "effort": "medium",
            "terminal_width": 160,
        }
    )
    assert "Gemini 3.8 Flash  medium" in no_icon_lines[0]
    assert "think:" not in no_icon_lines[0]
    assert "🧠" not in no_icon_lines[0]


@pytest.mark.parametrize(
    ("vim_mode", "expected_char", "expected_color"),
    [
        ("insert", "I", GREEN),
        ("INSERT", "I", GREEN),
        ("i", "I", GREEN),
        ("normal", "N", CYAN),
        ("n", "N", CYAN),
        ("visual", "V", MAGENTA),
        ("v", "V", MAGENTA),
        ("v-line", "V", MAGENTA),
        ("v-block", "V", MAGENTA),
        ("replace", "R", RED),
        ("r", "R", RED),
        ("command", "C", YELLOW),
        ("c", "C", YELLOW),
        ("select", "S", DIM),
    ],
)
def test_vim_mode_compact_badge_and_no_icons_fallback(
    monkeypatch: pytest.MonkeyPatch, vim_mode: str, expected_char: str, expected_color: str
) -> None:
    raw = {"agent_state": "idle", "vim_mode": vim_mode, "terminal_width": 120}
    ansi = render_statusline(decode_payload(raw), None)
    assert f"{expected_color}\ue7c5{expected_char}" in ansi
    assert strip_ansi(ansi) == f"[idle] \ue7c5{expected_char}"

    monkeypatch.setenv("TERMSTATUS_NO_ICONS", "1")
    ansi_no_icons = render_statusline(decode_payload(raw), None)
    assert f"{expected_color}{expected_char}" in ansi_no_icons
    assert "\ue7c5" not in ansi_no_icons
    assert strip_ansi(ansi_no_icons) == f"[idle] {expected_char}"


def test_plan_tier_on_usage_row_drops_before_cost_on_narrow_width() -> None:
    raw = {
        "agent_state": "idle",
        "context_window": {"remaining_percentage": 100},
        "quota": {"gemini-5h": {"remaining_percentage": 80}},
        "cost": {"estimated": 0.12},
        "plan_tier": "Google AI Pro",
        "terminal_width": 120,
    }
    wide = render_statusline(decode_payload(raw), None)
    wide_lines = strip_ansi(wide).splitlines()
    assert "Google AI Pro" not in wide_lines[0]
    assert "$0.12" in wide_lines[1]
    assert "Google AI Pro" in wide_lines[1]
    assert f"{DIM}Google AI Pro" in wide

    # Width 40 fits ctx + 5h badge + $0.12, but drops Google AI Pro first
    narrow_lines = rendered({**raw, "terminal_width": 40})
    assert "$0.12" in narrow_lines[1]
    assert "Google AI Pro" not in narrow_lines[1]


def test_standard_payload_row0_fits_under_80_cols_at_width_120() -> None:
    standard = {
        "agent_state": "idle",
        "cwd": "/work/repo",
        "model": {"display_name": "Gemini 4 Neon (Medium)", "effort": "medium"},
        "cycle_mode": "accept-edits",
        "sandbox": {"enabled": False},
        "plan_tier": "Google AI Pro",
        "vim": {"mode": "INSERT"},
        "context_window": {"remaining_percentage": 100},
        "quota": {
            "gemini-5h": {"remaining_fraction": 0.03, "reset_in_seconds": 12044},
            "gemini-weekly": {"remaining_fraction": 0.51, "reset_in_seconds": 580844},
        },
        "terminal_width": 120,
    }
    lines = rendered(standard)
    assert display_width(lines[0]) < 80
    assert "[idle] \ue7c5I" in lines[0]
    assert "Gemini 4 Neon" in lines[0]
    assert "accept-edits" in lines[0]
    assert "Google AI Pro" in lines[2]


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


@pytest.mark.parametrize(
    ("effort", "filled"),
    [
        ("off", 0),
        ("none", 0),
        ("low", 1),
        ("medium", 2),
        ("med", 2),
        ("high", 3),
        ("xhigh", 4),
        ("max", 5),
        ("0", 0),
        ("1", 1),
        ("2", 2),
        ("3", 3),
        ("4", 4),
        ("5", 5),
        ("9", 5),
    ],
)
def test_thinking_cellular_graph(effort: str, filled: int) -> None:
    graph = _thinking_cellular_graph(effort)
    assert strip_ansi(graph) == "▁▂▄▆█"
    assert graph.count("\x1b[36m") == filled
    assert graph.count("\x1b[90m") == 5 - filled


def test_thinking_cellular_graph_invalid_inputs() -> None:
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
