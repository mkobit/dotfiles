import json
import os
import pty
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND = [sys.executable, str(REPO_ROOT / "scripts/review-chezmoi-session.py")]
OPT_IN = "CHEZMOI_ENABLE_PERSONAL_SESSION_EVAL_CAPTURE"
SAMPLED_SESSION = "00000000-0000-0000-0000-000000000002"
TRANSCRIPT_PATH = "/private/session-eval-transcript-sentinel.jsonl"


@pytest.fixture
def capture_env(tmp_path):
    state = tmp_path / "state"
    env = {**os.environ, "XDG_STATE_HOME": str(state), OPT_IN: "1"}
    return env, state / "chezmoi-session-eval" / "codex"


def capture(env, cwd, session_id=SAMPLED_SESSION):
    result = subprocess.run(
        [*COMMAND, "capture"],
        cwd=REPO_ROOT,
        env=env,
        input=json.dumps(
            {
                "hook_event_name": "SessionEnd",
                "session_id": session_id,
                "cwd": str(cwd),
                "transcript_path": TRANSCRIPT_PATH,
            }
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert TRANSCRIPT_PATH not in result.stdout + result.stderr


def test_capture_creates_one_private_empty_marker(capture_env):
    env, queue = capture_env
    cwd = REPO_ROOT / "src/chezmoi"
    capture(env, cwd)
    capture(env, cwd)

    marker = queue / SAMPLED_SESSION
    assert list(queue.iterdir()) == [marker]
    assert marker.is_dir()
    assert stat.S_IMODE(marker.stat().st_mode) & 0o077 == 0
    assert list(marker.iterdir()) == []


@pytest.mark.parametrize(
    ("opt_in", "session_id", "foreign_repo"),
    [
        pytest.param(None, SAMPLED_SESSION, False, id="opt-in-unset"),
        pytest.param("0", SAMPLED_SESSION, False, id="opt-in-disabled"),
        pytest.param("1", "00000000-0000-0000-0000-000000000001", False, id="not-sampled"),
        pytest.param("1", "../invalid", False, id="invalid-id"),
        pytest.param("1", SAMPLED_SESSION, True, id="foreign-repository"),
    ],
)
def test_capture_skips_ineligible_sessions(tmp_path, capture_env, opt_in, session_id, foreign_repo):
    env, queue = capture_env
    env.pop(OPT_IN)
    if opt_in is not None:
        env[OPT_IN] = opt_in
    cwd = REPO_ROOT / "src/chezmoi"
    if foreign_repo:
        cwd = tmp_path / "other-repository"
        subprocess.run(["git", "init", "--quiet", str(cwd)], check=True, timeout=10)

    capture(env, cwd, session_id)

    assert not queue.exists() or list(queue.iterdir()) == []
    assert not (queue.parent / "invalid").exists()


def review(env, answer):
    master, terminal = pty.openpty()
    try:
        os.write(master, f"{answer}\n".encode())
        return subprocess.run(
            COMMAND,
            cwd=REPO_ROOT,
            env=env,
            stdin=terminal,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    finally:
        os.close(master)
        os.close(terminal)


@pytest.mark.parametrize(
    ("answer", "codex_status"),
    [
        pytest.param("n", 0, id="declined"),
        pytest.param("y", 1, id="fork-failed"),
        pytest.param("y", 0, id="fork-succeeded"),
    ],
)
def test_review_requires_confirmation_and_consumes_only_successful_forks(tmp_path, capture_env, answer, codex_status):
    env, queue = capture_env
    checkout = tmp_path / "skills"
    skill = checkout / ".agents/skills/session-eval-review/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: session-eval-review\ndescription: Review a session.\n---\n")
    calls = tmp_path / "codex-calls.jsonl"
    codex = tmp_path / "codex"
    codex.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"with open({str(calls)!r}, 'a') as log:\n"
        f"    log.write(json.dumps([sys.argv[1:], {OPT_IN!r} in os.environ]) + '\\n')\n"
        f"sys.exit({codex_status})\n"
    )
    codex.chmod(0o700)
    env["CHEZMOI_SKILLS_CHECKOUT"] = str(checkout)
    env["PATH"] = os.pathsep.join([str(tmp_path), env["PATH"]])
    capture(env, REPO_ROOT / "src/chezmoi")
    marker = queue / SAMPLED_SESSION
    assert marker.is_dir()

    result = review(env, answer)

    if answer == "n":
        assert result.returncode == 0, result.stderr
        assert list(queue.iterdir()) == [marker]
        assert not calls.exists()
        return

    recorded_calls = calls.read_text()
    ((argv, has_opt_in),) = [json.loads(line) for line in recorded_calls.splitlines()]
    assert argv[:5] == ["fork", "--no-daemon", "--cd", str(checkout), SAMPLED_SESSION]
    assert any("$session-eval-review" in argument for argument in argv[5:])
    assert has_opt_in is False
    next_result = review(env, "y")
    if codex_status:
        assert list(queue.iterdir()) == [marker]
        assert calls.read_text() == recorded_calls * 2
    else:
        assert result.returncode == 0, result.stderr
        assert next_result.returncode == 0, next_result.stderr
        assert calls.read_text() == recorded_calls
