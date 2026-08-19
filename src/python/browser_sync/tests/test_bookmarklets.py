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
