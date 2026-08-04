"""Tests for generated Chrome site-search shortcut sync payloads."""

import pytest

from browser_sync import _terminal
from browser_sync.shortcuts import _build_sync_script, _Shortcut

_SHORTCUTS = (_Shortcut(keyword="@stripe", name="Stripe", url="https://go/search/%s"),)


def test_apply_payload_enables_additions_and_removals() -> None:
    script = _build_sync_script(_SHORTCUTS, prune=True, confirm_removal=True)

    assert "const applyAdditions = true;" in script
    assert "const confirmRemoval = true;" in script
    assert "const prune = true;" in script


def test_exclude_removals_payload_only_applies_additions() -> None:
    script = _build_sync_script(_SHORTCUTS)

    assert "const applyAdditions = true;" in script
    assert "const confirmRemoval = false;" in script
    assert "const prune = false;" in script


def test_dry_run_payload_gates_all_mutations() -> None:
    script = _build_sync_script(_SHORTCUTS, prune=True, apply_additions=False)

    assert "const applyAdditions = false;" in script
    assert "const confirmRemoval = false;" in script
    assert "const prune = true;" in script
    assert "WOULD-ADD" in script
    assert "WOULD-DEL" in script


@pytest.mark.parametrize(("key", "expected"), [("\r", "prune"), ("x", "exclude_removals"), ("d", "dry_run")])
def test_shortcut_sync_mode_selects_payload(monkeypatch: pytest.MonkeyPatch, key: str, expected: str) -> None:
    monkeypatch.setattr(_terminal, "getkey", lambda: key)

    assert _terminal.prompt_shortcut_sync_mode() == expected
