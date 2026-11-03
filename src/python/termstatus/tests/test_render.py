from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payload import StatusLineStdIn
from termstatus.render import render_lines


def test_render_lines_groups_by_line_and_aligns_columns():
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
    assert len(lines) == 5

    assert "A0" in lines[1] and "A10" in lines[1]
    assert "B0" in lines[2]
    assert "B10" not in lines[2]
    assert "C0" in lines[3] and "C10" in lines[3]


def test_render_lines_narrow_terminal():
    payload = StatusLineStdIn()

    segments = [
        SegmentGenerationResult(
            line=0, index=0, segment=Segment(text="Long text that would usually wrap or exceed narrow width")
        ),
        SegmentGenerationResult(line=0, index=10, segment=Segment(text="More text")),
    ]

    lines = render_lines(payload, None, segments, terminal_width=40)

    # Output with Rich Panel should have borders (top and bottom) + content = at least 3 lines.
    assert len(lines) >= 3
    assert any(line.strip() for line in lines)
