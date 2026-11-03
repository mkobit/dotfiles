import pytest

from termstatus.payload import (
    AgentInfo,
    ContextWindowInfo,
    CostInfo,
    ModelInfo,
    OutputStyle,
    StatusLineStdIn,
)
from termstatus.segments.claude import (
    _format_tokens_compact,
    format_context_usage,
    format_cost,
    format_model_info,
    format_session_info,
)
from termstatus.segments.constants import (
    BRIGHT_GREEN,
    GREEN,
    ORANGE,
    RED,
    YELLOW,
)


class TestFormatTokensCompact:
    def test_small_values(self) -> None:
        assert _format_tokens_compact(0) == "0"
        assert _format_tokens_compact(999) == "999"

    def test_k_suffix(self) -> None:
        assert _format_tokens_compact(1000) == "1k"
        assert _format_tokens_compact(1100) == "1.1k"
        assert _format_tokens_compact(10000) == "10k"
        assert _format_tokens_compact(50000) == "50k"

    def test_m_suffix(self) -> None:
        assert _format_tokens_compact(1000000) == "1M"
        assert _format_tokens_compact(1500000) == "1.5M"


class TestFormatContextUsage:
    @pytest.mark.parametrize(
        ("used_pct", "expected_color"),
        [
            (10.0, BRIGHT_GREEN),  # 90% remaining — >=85
            (20.0, GREEN),  # 80% remaining — >=70
            (40.0, YELLOW),  # 60% remaining — >=55
            (60.0, ORANGE),  # 40% remaining — >=30
            (92.0, RED),  # 8% remaining  — <30
        ],
    )
    def test_color_by_remaining(self, used_pct: float, expected_color: str) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=used_pct))
        assert res is not None
        assert expected_color in " ".join([r.segment.text for r in res])

    def test_remaining_pct_shown(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=22.0))
        assert res is not None
        assert "78%" in " ".join([r.segment.text for r in res])

    def test_token_counts_shown_when_window_known(self) -> None:
        cw = ContextWindowInfo(
            total_input_tokens=40000,
            total_output_tokens=10000,
            context_window_size=200000,
            used_percentage=25.0,
        )
        res = format_context_usage(cw)
        assert res is not None
        assert "50k" in " ".join([r.segment.text for r in res])
        assert "200k" in " ".join([r.segment.text for r in res])

    def test_no_token_counts_without_window_size(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=50.0))
        assert res is not None
        assert "/" not in " ".join([r.segment.text for r in res])

    def test_zero_usage_defaults_to_bright_green(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=None))
        assert res is not None
        assert BRIGHT_GREEN in " ".join([r.segment.text for r in res])

    def test_placed_on_context_line(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=50.0))
        assert res is not None
        assert (res[0].line if res else None) == 10


class TestFormatModelInfo:
    def test_model_name_present(self) -> None:
        payload = StatusLineStdIn(model=ModelInfo(display_name="Sonnet 4.6"))
        res = format_model_info(payload)
        assert res is not None
        assert "Sonnet 4.6" in " ".join([r.segment.text for r in res])

    def test_output_style_present(self) -> None:
        payload = StatusLineStdIn(
            model=ModelInfo(display_name="X"),
            output_style=OutputStyle(name="concise"),
        )
        res = format_model_info(payload)
        assert res is not None
        assert "[concise]" in " ".join([r.segment.text for r in res])

    def test_no_output_style_when_absent(self) -> None:
        payload = StatusLineStdIn(model=ModelInfo(display_name="X"))
        res = format_model_info(payload)
        assert res is not None
        assert "concise" not in " ".join([r.segment.text for r in res])
        assert "default" not in " ".join([r.segment.text for r in res])

    def test_agent_name_present(self) -> None:
        payload = StatusLineStdIn(
            model=ModelInfo(display_name="X"),
            agent=AgentInfo(name="my-agent"),
        )
        res = format_model_info(payload)
        assert res is not None
        assert "my-agent" in " ".join([r.segment.text for r in res])


class TestFormatSessionInfo:
    def test_session_id_hash_not_shown(self) -> None:
        payload = StatusLineStdIn(session_id="abc123def456")
        res = format_session_info(payload)
        assert res == []

    def test_timer_formatted(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_duration_ms=3_661_000))
        res = format_session_info(payload)
        assert res is not None
        assert "01:01:01" in " ".join([r.segment.text for r in res])

    def test_returns_none_with_no_data(self) -> None:
        res = format_session_info(StatusLineStdIn())
        assert res == []


class TestFormatCost:
    def test_cost_shown(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=1.23))
        res = format_cost(payload)
        assert res is not None
        assert "1.23" in " ".join([r.segment.text for r in res])

    def test_returns_none_when_zero(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=0.0))
        res = format_cost(payload)
        assert res == []

    def test_placed_on_usage_line(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=0.5))
        res = format_cost(payload)
        assert res is not None
        assert (res[0].line if res else None) == 9
