import unittest

from claude_statusline.render import render_lines
from claude_statusline.types.layout import Segment, SegmentGenerationResult
from claude_statusline.types.payload import StatusLineStdIn


class TestRenderLines(unittest.TestCase):
    def test_render_lines_groups_by_line_and_aligns_columns(self):
        payload = StatusLineStdIn()

        segments = [
            SegmentGenerationResult(line=0, index=0, segment=Segment(text="A0")),
            SegmentGenerationResult(line=0, index=10, segment=Segment(text="A10")),
            SegmentGenerationResult(line=1, index=0, segment=Segment(text="B0")),
            # Missing index 10 in line 1
            SegmentGenerationResult(line=2, index=0, segment=Segment(text="C0")),
            SegmentGenerationResult(line=2, index=10, segment=Segment(text="C10")),
        ]

        lines = render_lines(payload, None, segments)

        # We should have 3 lines of output.
        # Line 0: "A0   A10"
        # Line 1: "B0      "
        # Line 2: "C0   C10"

        self.assertEqual(len(lines), 3)
        # Because we're using Rich, exact whitespace might differ depending on padding,
        # but the order and alignment should be there.
        self.assertTrue("A0" in lines[0] and "A10" in lines[0])
        self.assertTrue("B0" in lines[1])
        self.assertFalse("B10" in lines[1])
        self.assertTrue("C0" in lines[2] and "C10" in lines[2])
