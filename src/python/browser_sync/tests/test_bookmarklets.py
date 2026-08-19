"""Tests for bookmarklet JS-to-URL conversion."""

from pathlib import Path

import pytest

from browser_sync.bookmarklets import _get_desired, _js_to_bookmarklet_url


def test_strips_title_directive() -> None:
    source = "// title: Example\nconst a = 1;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1;"


def test_inline_comment_does_not_swallow_subsequent_lines() -> None:
    # Regression: collapsing newlines to spaces turned a trailing "// note" into a
    # comment covering the rest of the script, eating the closing braces and
    # producing "Unexpected end of input" when the bookmarklet ran.
    source = "// title: Example\nconst a = 1; // note\nconst b = 2;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1; const b = 2;"


def test_comment_only_line_is_removed() -> None:
    source = "// title: Example\n// just a note\nconst a = 1;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1;"


def test_double_slash_inside_string_is_not_treated_as_comment() -> None:
    source = '// title: Example\nconst url = "https://go/x"; // real comment\n'

    assert _js_to_bookmarklet_url(source) == 'javascript:const url = "https://go/x";'


def test_source_without_comments_is_unchanged_from_prior_collapsing_behavior() -> None:
    # Files with no // comments must produce the exact same collapsed output as
    # before, so fixing the comment bug doesn't force an unrelated re-sync of
    # every other bookmarklet.
    source = "// title: Example\nconst a = 1;\nconst b = 2;\n"

    assert _js_to_bookmarklet_url(source) == "javascript:const a = 1; const b = 2;"


def test_get_desired_rejects_a_bookmarklet_that_is_not_valid_javascript(tmp_path: Path) -> None:
    # A backstop for the whole class of encoding bugs: whatever produced a broken
    # bookmarklet, catch it here instead of a SyntaxError in the browser.
    (tmp_path / "broken.js").write_text("// title: Broken\nconst a = (1;\n")

    with pytest.raises(SystemExit):
        _get_desired(tmp_path)


def test_get_desired_accepts_valid_javascript(tmp_path: Path) -> None:
    (tmp_path / "fine.js").write_text("// title: Fine\nconst a = 1;\n")

    assert _get_desired(tmp_path) == {"Fine": "javascript:const a = 1;"}
