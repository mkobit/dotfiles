import re
import subprocess
import tempfile
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


def _first_non_blank_line(text):
    return next((line for line in text.splitlines() if line.strip()), "")


def test_shellcheck(shellcheck_candidate, host, chezmoi_command):
    render = host.run(chezmoi_command("execute-template", "-f", "--with-stdin", shellcheck_candidate["sourceAbsolute"]))
    assert render.rc == 0, f"template render failed:\n{render.stderr}"

    first_line = _first_non_blank_line(render.stdout)
    if not _classify_shebang(first_line):
        pytest.skip("renders to non-shell content")

    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as rendered_file:
        rendered_file.write(render.stdout)
        rendered_path = rendered_file.name

    try:
        result = subprocess.run(["shellcheck", "-x", rendered_path], capture_output=True, text=True, check=False)
    finally:
        Path(rendered_path).unlink()

    assert result.returncode == 0, result.stdout
