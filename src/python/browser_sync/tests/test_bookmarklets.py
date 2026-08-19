"""Tests for bookmarklet JS-to-URL conversion."""

from browser_sync.bookmarklets import _js_to_bookmarklet_url


def test_strips_title_directive() -> None:
    source = "// title: Example\nconst a = 1;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1;"


def test_inline_comment_does_not_swallow_subsequent_lines() -> None:
    # Regression: collapsing newlines to spaces turned a trailing "// note" into a
    # comment covering the rest of the script, eating the closing braces and
    # producing "Unexpected end of input" when the bookmarklet ran.
    source = "// title: Example\nconst a = 1; // note\nconst b = 2;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1; // note\nconst b = 2;"
