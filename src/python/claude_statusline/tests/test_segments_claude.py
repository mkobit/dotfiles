import unittest

from claude_statusline.models import (
    AgentInfo,
    ContextWindowInfo,
    CostInfo,
    ModelInfo,
    OutputStyle,
    StatusLineStdIn,
)
from claude_statusline.segments.claude import (
    format_context_usage,
    format_cost,
    format_model_info,
    format_session_info,
)
from claude_statusline.segments.constants import (
    BRIGHT_GREEN,
    GREEN,
    ORANGE,
    RED,
    YELLOW,
)


class TestFormatContextUsage(unittest.TestCase):
    def test_color_by_remaining(self) -> None:
        cases = [
            (10.0, BRIGHT_GREEN),  # 90% remaining — >=85
            (20.0, GREEN),  # 80% remaining — >=70
            (40.0, YELLOW),  # 60% remaining — >=55
            (60.0, ORANGE),  # 40% remaining — >=30
            (92.0, RED),  # 8% remaining  — <30
        ]
        for used_pct, expected_color in cases:
            with self.subTest(used_pct=used_pct):
                res = format_context_usage(ContextWindowInfo(used_percentage=used_pct))
                assert res is not None
                self.assertIn(expected_color, res.segment.text)

    def test_battery_icon_present(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=22.0))
        assert res is not None
        self.assertIn("78%", res.segment.text)

    def test_token_counts_shown_when_window_known(self) -> None:
        cw = ContextWindowInfo(
            total_input_tokens=40000,
            total_output_tokens=10000,
            context_window_size=200000,
            used_percentage=25.0,
        )
        res = format_context_usage(cw)
        assert res is not None
        self.assertIn("50k", res.segment.text)
        self.assertIn("200k", res.segment.text)

    def test_no_token_counts_without_window_size(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=50.0))
        assert res is not None
        self.assertNotIn("/", res.segment.text)

    def test_zero_usage_defaults_to_bright_green(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=None))
        assert res is not None
        self.assertIn(BRIGHT_GREEN, res.segment.text)

    def test_placed_on_line_2(self) -> None:
        res = format_context_usage(ContextWindowInfo(used_percentage=50.0))
        assert res is not None
        self.assertEqual(res.line, 2)


class TestFormatModelInfo(unittest.TestCase):
    def test_model_name_present(self) -> None:
        payload = StatusLineStdIn(model=ModelInfo(display_name="Sonnet 4.6"))
        res = format_model_info(payload)
        assert res is not None
        self.assertIn("Sonnet 4.6", res.segment.text)

    def test_output_style_present(self) -> None:
        payload = StatusLineStdIn(
            model=ModelInfo(display_name="X"),
            output_style=OutputStyle(name="concise"),
        )
        res = format_model_info(payload)
        assert res is not None
        self.assertIn("[concise]", res.segment.text)

    def test_no_output_style_when_absent(self) -> None:
        payload = StatusLineStdIn(model=ModelInfo(display_name="X"))
        res = format_model_info(payload)
        assert res is not None
        self.assertNotIn("concise", res.segment.text)
        self.assertNotIn("default", res.segment.text)

    def test_agent_name_present(self) -> None:
        payload = StatusLineStdIn(
            model=ModelInfo(display_name="X"),
            agent=AgentInfo(name="my-agent"),
        )
        res = format_model_info(payload)
        assert res is not None
        self.assertIn("my-agent", res.segment.text)


class TestFormatSessionInfo(unittest.TestCase):
    def test_session_name_shown(self) -> None:
        payload = StatusLineStdIn(session_name="my-session")
        res = format_session_info(payload)
        assert res is not None
        self.assertIn("my-session", res.segment.text)

    def test_session_id_hash_not_shown(self) -> None:
        payload = StatusLineStdIn(session_id="abc123def456")
        res = format_session_info(payload)
        self.assertIsNone(res)

    def test_timer_formatted(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_duration_ms=3_661_000))
        res = format_session_info(payload)
        assert res is not None
        self.assertIn("01:01:01", res.segment.text)

    def test_returns_none_with_no_data(self) -> None:
        res = format_session_info(StatusLineStdIn())
        self.assertIsNone(res)


class TestFormatCost(unittest.TestCase):
    def test_cost_shown(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=1.23))
        res = format_cost(payload)
        assert res is not None
        self.assertIn("1.23", res.segment.text)

    def test_returns_none_when_zero(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=0.0))
        res = format_cost(payload)
        self.assertIsNone(res)

    def test_placed_on_line_2(self) -> None:
        payload = StatusLineStdIn(cost=CostInfo(total_cost_usd=0.5))
        res = format_cost(payload)
        assert res is not None
        self.assertEqual(res.line, 2)


if __name__ == "__main__":
    unittest.main()
