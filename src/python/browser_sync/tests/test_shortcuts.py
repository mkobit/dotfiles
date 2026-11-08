"""Tests for generated Chrome site-search shortcut sync payloads."""

import pytest

from browser_sync._terminal import _shortcut_mode_for_key
from browser_sync.shortcuts import _build_sync_script, _Shortcut

_SHORTCUTS = (_Shortcut(keyword="@stripe", name="Stripe", url="https://go/search/%s"),)


@pytest.mark.parametrize(
    ("kwargs", "expected_snippets"),
    [
        (
            {"prune": True, "confirm_removal": True},
            ("const applyAdditions = true;", "const confirmRemoval = true;", "const prune = true;"),
        ),
        (
            {},
            ("const applyAdditions = true;", "const confirmRemoval = false;", "const prune = false;"),
        ),
        (
            {"prune": True, "apply_additions": False},
            (
                "const applyAdditions = false;",
                "const confirmRemoval = false;",
                "const prune = true;",
                "WOULD-ADD",
                "WOULD-DEL",
            ),
        ),
    ],
    ids=["apply", "exclude_removals", "dry_run"],
)
def test_build_sync_script_payload_modes(kwargs: dict[str, bool], expected_snippets: tuple[str, ...]) -> None:
    script = _build_sync_script(_SHORTCUTS, **kwargs)
    for snippet in expected_snippets:
        assert snippet in script


@pytest.mark.parametrize(
    ("key", "expected_mode"),
    [
        ("p", "prune"),
        ("x", "exclude_removals"),
        ("d", "dry_run"),
        ("q", None),
        ("\r", None),
    ],
)
def test_shortcut_mode_for_key(key: str, expected_mode: str | None) -> None:
    assert _shortcut_mode_for_key(key) == expected_mode
