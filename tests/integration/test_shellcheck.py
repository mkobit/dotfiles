import re
from pathlib import Path

import pytest

_SHEBANG_RE = re.compile(r"^#!\s*(?P<interpreter>\S+)(?:\s+(?P<rest>.*))?$")


def _classify_shebang(first_line):
    match = _SHEBANG_RE.match(first_line)
    if not match:
        return False

    interpreter = Path(match.group("interpreter")).name
    if interpreter in ("bash", "sh"):
        return True

    if interpreter != "env":
        return False

    tokens = (match.group("rest") or "").split()
    for token in tokens:
        if token.startswith("-"):
            continue
        return Path(token).name in ("bash", "sh")
    return False


@pytest.mark.parametrize(
    ("first_line", "expected"),
    [
        ("#!/bin/bash", True),
        ("#!/bin/sh", True),
        ("#!/usr/bin/env bash", True),
        ("#!/usr/bin/env sh", True),
        ("#!/usr/bin/env -S bash", True),
        ("#!/bin/bash -e", True),
        ("#! /bin/sh", True),
        ("#!/usr/bin/env python3", False),
        ("#!/usr/bin/env", False),
        ("{", False),
        ("", False),
        ("# just a comment", False),
    ],
)
def test_classify_shebang(first_line, expected):
    assert _classify_shebang(first_line) is expected


def test_shellcheck_candidate_has_required_keys(shellcheck_candidate):
    assert "sourceRelative" in shellcheck_candidate
    assert "sourceAbsolute" in shellcheck_candidate
