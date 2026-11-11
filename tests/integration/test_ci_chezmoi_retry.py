import os
import subprocess
import textwrap
from pathlib import Path

import pytest


def workflow_script(name):
    workflow = (Path.cwd() / ".github/workflows/ci.yml").read_text()
    step = workflow.split(f"      - name: {name}\n", 1)[1].split("\n      - name:", 1)[0]
    return textwrap.dedent(step.split("        run: |\n", 1)[1])


@pytest.fixture
def retry_workflow(tmp_path):
    commands = tmp_path / "bin"
    commands.mkdir()
    stub = commands / "chezmoi"
    stub.write_text("""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$TEST_CALLS"
if [[ " $* " == *" --dry-run "* ]]; then
  attempt=0
  if [[ -f "$TEST_ATTEMPTS" ]]; then
    attempt=$(cat "$TEST_ATTEMPTS")
  fi
  attempt=$((attempt + 1))
  printf '%s\\n' "$attempt" > "$TEST_ATTEMPTS"
  [[ "$attempt" -ge "$TEST_SUCCEED_AT" ]]
else
  exit "$TEST_APPLY_EXIT"
fi
""")
    stub.chmod(0o755)
    sleep = commands / "sleep"
    sleep.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$TEST_SLEEPS"\n')
    sleep.chmod(0o755)
    calls = tmp_path / "calls"
    sleeps = tmp_path / "sleeps"
    env = {
        **os.environ,
        "PATH": f"{commands}:{os.environ['PATH']}",
        "RUNNER_TEMP": str(tmp_path),
        "CHEZMOI_CACHE_DIR": str(tmp_path / "cache"),
        "CHEZMOI_CONFIG": str(tmp_path / "config"),
        "GITHUB_WORKSPACE": str(tmp_path / "source"),
        "CHEZMOI_DEST": str(tmp_path / "dest"),
        "TEST_CALLS": str(calls),
        "TEST_SLEEPS": str(sleeps),
        "TEST_ATTEMPTS": str(tmp_path / "attempts"),
        "TEST_SUCCEED_AT": "1",
        "TEST_APPLY_EXIT": "0",
    }

    def run(succeed_at=1, apply_exit=0):
        env.update(TEST_SUCCEED_AT=str(succeed_at), TEST_APPLY_EXIT=str(apply_exit))
        prefetch = subprocess.run(
            ["bash", "-e", "-c", workflow_script("Prefetch chezmoi externals")],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        apply = None
        if prefetch.returncode == 0:
            apply = subprocess.run(
                ["bash", "-e", "-c", workflow_script("Run chezmoi apply")],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        return (
            prefetch,
            apply,
            calls.read_text().splitlines(),
            sleeps.read_text().splitlines() if sleeps.exists() else [],
        )

    return run


@pytest.mark.parametrize("succeed_at", [1, 5])
def test_prefetch_retries_downloads_then_applies_once(retry_workflow, succeed_at):
    prefetch, apply, calls, sleeps = retry_workflow(succeed_at=succeed_at)
    assert prefetch.returncode == 0
    assert apply.returncode == 0
    assert len(calls) == succeed_at + 1
    assert all("--dry-run --exclude=scripts" in call for call in calls[:-1])
    assert "--dry-run" not in calls[-1]
    assert sleeps == ["15", "30", "60", "120"][: succeed_at - 1]


def test_prefetch_stops_after_five_failures(retry_workflow):
    prefetch, apply, calls, sleeps = retry_workflow(succeed_at=6)
    assert prefetch.returncode == 1
    assert apply is None
    assert len(calls) == 5
    assert sleeps == ["15", "30", "60", "120"]


def test_apply_failure_is_not_retried(retry_workflow):
    prefetch, apply, calls, sleeps = retry_workflow(apply_exit=42)
    assert prefetch.returncode == 0
    assert apply.returncode == 42
    assert len(calls) == 2
    assert sleeps == []
