"""Tests for bookmarklet JS-to-URL conversion."""

import subprocess

from browser_sync.bookmarklets import _js_to_bookmarklet_url


def _assert_valid_javascript(url: str) -> None:
    """Fail the test if the bookmarklet body doesn't parse as JavaScript.

    Guards the whole class of encoding bugs (e.g. a comment swallowing the rest of the
    script) in CI, rather than only surfacing as a SyntaxError when someone clicks it.
    """
    code = url.removeprefix("javascript:")
    result = subprocess.run(["node", "--check", "-"], input=code, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_strips_title_directive() -> None:
    source = "// title: Example\nconst a = 1;\n"
    url = _js_to_bookmarklet_url(source)

    assert url == "javascript:const a = 1;"
    _assert_valid_javascript(url)


def test_inline_comment_does_not_swallow_subsequent_lines() -> None:
    # Regression: collapsing newlines to spaces turned a trailing "// note" into a
    # comment covering the rest of the script, eating the closing braces and
    # producing "Unexpected end of input" when the bookmarklet ran.
    source = "// title: Example\nconst a = 1; // note\nconst b = 2;\n"
    url = _js_to_bookmarklet_url(source)

    assert url == "javascript:const a = 1; const b = 2;"
    _assert_valid_javascript(url)


def test_comment_only_line_is_removed() -> None:
    source = "// title: Example\n// just a note\nconst a = 1;\n"
    url = _js_to_bookmarklet_url(source)

    assert url == "javascript:const a = 1;"
    _assert_valid_javascript(url)


def test_double_slash_inside_string_is_not_treated_as_comment() -> None:
    source = '// title: Example\nconst url = "https://go/x"; // real comment\n'
    url = _js_to_bookmarklet_url(source)

    assert url == 'javascript:const url = "https://go/x";'
    _assert_valid_javascript(url)


def test_source_without_comments_is_unchanged_from_prior_collapsing_behavior() -> None:
    # Files with no // comments must produce the exact same collapsed output as
    # before, so fixing the comment bug doesn't force an unrelated re-sync of
    # every other bookmarklet.
    source = "// title: Example\nconst a = 1;\nconst b = 2;\n"
    url = _js_to_bookmarklet_url(source)

    assert url == "javascript:const a = 1; const b = 2;"
    _assert_valid_javascript(url)


def test_realistic_bookmarklet_with_every_hazard_at_once() -> None:
    # Mirrors add-stripe-id-links.js's actual shape: a leading full-line comment, a
    # regex literal, URL strings containing "//", and a trailing inline comment.
    source = """\
// title: Example
(function () {
  // full-line comment before any code
  const pattern = /\\bfoo\\b/g;
  const template = "https://go/x/%s";
  pattern.lastIndex = 0; // reset before reuse
})();
"""
    url = _js_to_bookmarklet_url(source)

    _assert_valid_javascript(url)
