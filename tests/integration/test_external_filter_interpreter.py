"""Guard the interpreter that chezmoi externals use as filter.command.

Regression this locks down: ai-agents.toml.tmpl used a bare "python3", which
PATH-resolves through a version-manager shim on any machine running pyenv or
mise. A shim costs ~900ms per spawn against ~30ms for a real interpreter, and
that template alone renders 128 externals, so the bare name turned a single
apply into roughly two minutes of pure process startup. It also meant the
filter ran on whatever version the shim's own config named, which is state
this repo never declared.

Every external template is rendered and checked, so a newly added one that
reintroduces a bare name or a shim fails here without anyone wiring it up.
"""

import functools
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

# skill_filter declares requires-python >= 3.8 as its runtime contract; the
# resolver may pick something newer for startup speed but must never go below.
MINIMUM_VERSION = (3, 8)

_VERSION_RE = re.compile(r"(\d+)\.(\d+)")


@functools.cache
def _interpreter_version(command):
    """Return (major, minor) for an interpreter, or None if it won't report one."""
    result = subprocess.run([command, "--version"], capture_output=True, text=True, check=False)
    match = _VERSION_RE.search(f"{result.stdout}\n{result.stderr}")
    return (int(match.group(1)), int(match.group(2))) if match else None


def _argument_problems(template_name, target, args):
    """Yield a description for each way this filter's argv gives up startup cost."""
    where = f"{template_name}: external {target!r} filter.args = {args!r}"

    # -S skips site-packages scanning. The saving depends on how much is installed
    # in the interpreter being used, so it is insurance against the bad case rather
    # than a fixed win; dropping it silently regresses every one of these spawns.
    if "-S" not in args:
        yield f"{where} is missing -S; see src/python/skill_filter/README.md"


def _problems(template_name, target, command):
    """Yield a description for each way this filter.command is unsafe."""
    where = f"{template_name}: external {target!r} filter.command = {command!r}"

    if not command.startswith("/"):
        yield f"{where} is not an absolute path; a bare name resolves through PATH and lands on shims"
        return

    if "/shims/" in command:
        yield f"{where} is a version-manager shim; use the real interpreter path"
        return

    path = Path(command)
    if not path.is_file():
        yield f"{where} does not exist"
        return
    if not path.stat().st_mode & 0o111:
        yield f"{where} is not executable"
        return

    version = _interpreter_version(command)
    if version is None:
        yield f"{where} did not report a version"
    elif version < MINIMUM_VERSION:
        expected = ".".join(str(part) for part in MINIMUM_VERSION)
        found = ".".join(str(part) for part in version)
        yield f"{where} is python {found}, below the declared {expected} floor"


@pytest.mark.integration
def test_external_filter_commands_are_pinned_real_interpreters(chezmoi_source_root, host, chezmoi_command):
    """Every rendered external's filter.command must be an absolute, non-shim, supported interpreter."""
    templates = sorted((chezmoi_source_root / ".chezmoiexternals").glob("*.tmpl"))
    assert templates, f"no external templates found under {chezmoi_source_root / '.chezmoiexternals'}"

    problems = []
    filters_checked = 0

    for template in templates:
        render = host.run(chezmoi_command("execute-template", "-f", str(template)))
        assert render.rc == 0, f"{template.name} failed to render:\n{render.stderr}"
        if not render.stdout.strip():
            continue

        for target, entry in tomllib.loads(render.stdout).items():
            if not isinstance(entry, dict):
                continue
            filter_spec = entry.get("filter", {})
            command = filter_spec.get("command")
            if command is None:
                continue
            filters_checked += 1
            problems.extend(_problems(template.name, target, command))
            problems.extend(_argument_problems(template.name, target, filter_spec.get("args", [])))

    assert filters_checked, "no externals declared a filter.command; this guard would silently pass"
    assert not problems, "unsafe external filter interpreters:\n" + "\n".join(problems)
