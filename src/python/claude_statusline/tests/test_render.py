import unittest

from claude_statusline.layout import Segment, SegmentGenerationResult
from claude_statusline.payload import StatusLineStdIn
from claude_statusline.render import render_lines


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

        # Output with Rich Panel should have borders (top and bottom) + 3 rows = 5 lines.
        self.assertEqual(len(lines), 5)

        self.assertTrue("A0" in lines[1] and "A10" in lines[1])
        self.assertTrue("B0" in lines[2])
        self.assertFalse("B10" in lines[2])
        self.assertTrue("C0" in lines[3] and "C10" in lines[3])
