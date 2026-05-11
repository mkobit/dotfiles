import os
import subprocess
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from termbud.main import app
from termbud.zellij import _extract, _fmt, _load_patterns

runner = CliRunner()

# Generic sample text with no relation to any specific org or product.
SAMPLE_SCROLLBACK = """
See https://en.wikipedia.org/wiki/Python_(programming_language) for info.
Also https://en.wikipedia.org/wiki/Zellij and https://fzf.netlify.app/docs.
Join #announcements or #help-desk in chat.
Ticket ref: DOC-00001A2B3C4D5E6F7 assigned to alice.
Internal link: go/onboarding or go/docs/setup.
"""

# Patterns that exercise the regex/url/prefix machinery with made-up schemas.
TICKET_PATTERN = {
    "label": "ticket",
    "regex": r"\b(DOC-[0-9A-F]{17})\b",
    "url": "https://issues.example.com/browse/{match}",
    "prefix": "",
}
CHAT_PATTERN = {
    "label": "chat channel",
    "regex": r"#([\w][\w-]+)",
    "url": "https://chat.example.com/channels/{match}",
    "prefix": "#",
}
SHORTLINK_PATTERN = {
    "label": "shortlink",
    "regex": r"\bgo/([\w/][\w/-]*)",
    "url": "https://links.example.com/{match}",
    "prefix": "go/",
}
BUILTIN_URL_PATTERN = {
    "label": "url",
    "regex": r'https?://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
    "url": "{match}",
    "prefix": "",
}


def _dump_screen_side_effect(text: str):
    def side_effect(cmd, *args, **kwargs):
        if cmd[:3] == ["zellij", "action", "dump-screen"]:
            Path(cmd[4]).write_text(text)
        return MagicMock()
    return side_effect


# --- extraction helpers ---

def test_extract_url():
    text = "visit https://en.wikipedia.org/wiki/Main_Page today"
    matches = _extract(text, [BUILTIN_URL_PATTERN])
    assert matches == [("url", "https://en.wikipedia.org/wiki/Main_Page", "{match}", "")]


def test_extract_custom_pattern():
    matches = _extract("ref DOC-00001A2B3C4D5E6F7 open", [TICKET_PATTERN])
    assert len(matches) == 1
    assert matches[0][:2] == ("ticket", "DOC-00001A2B3C4D5E6F7")


def test_extract_prefix_pattern_strips_prefix():
    matches = _extract("join #help-desk now", [CHAT_PATTERN])
    assert matches[0][1] == "help-desk"


def test_extract_deduplicates():
    matches = _extract("go/docs go/docs again", [SHORTLINK_PATTERN])
    assert len(matches) == 1


def test_extract_multiple_patterns():
    matches = _extract(SAMPLE_SCROLLBACK, [BUILTIN_URL_PATTERN, TICKET_PATTERN, CHAT_PATTERN, SHORTLINK_PATTERN])
    labels = [m[0] for m in matches]
    assert "url" in labels
    assert "ticket" in labels
    assert "chat channel" in labels
    assert "shortlink" in labels


def test_fmt_fixed_width_label():
    line = _fmt("ticket", "DOC-00001A2B3C4D5E6F7")
    assert "DOC-00001A2B3C4D5E6F7" in line
    assert len(line.split("]")[0]) == 17  # "[" + 16 chars padded


def test_load_patterns_missing_file():
    assert _load_patterns(Path("/nonexistent/patterns.toml")) == []


def test_load_patterns_from_file(tmp_path):
    toml = tmp_path / "patterns.toml"
    toml.write_text("""
[patterns.wiki]
label = "wikipedia"
regex = 'https://en\\.wikipedia\\.org/wiki/(\\S+)'
url = "https://en.wikipedia.org/wiki/{match}"
prefix = "wiki:"
""")
    patterns = _load_patterns(toml)
    assert len(patterns) == 1
    assert patterns[0]["label"] == "wikipedia"
    assert patterns[0]["prefix"] == "wiki:"


# --- pick command integration ---

def _pick_stack(extra_patches: dict | None = None):
    """ExitStack with os primitive mocks + execvp for pick command tests."""
    stack = ExitStack()
    stack.enter_context(patch("termbud.zellij.os.pipe", return_value=(3, 4)))
    stack.enter_context(patch("termbud.zellij.os.write"))
    stack.enter_context(patch("termbud.zellij.os.close"))
    stack.enter_context(patch("termbud.zellij.os.dup2"))
    execvp = stack.enter_context(patch("termbud.zellij.os.execvp"))
    execvp.side_effect = SystemExit(0)
    for target, value in (extra_patches or {}).items():
        stack.enter_context(patch(target, **value) if isinstance(value, dict) else patch(target, value))
    return stack, execvp


def test_pick_execs_fzf(tmp_path):
    patterns_file = tmp_path / "patterns.toml"
    patterns_file.write_text("""
[patterns.wiki]
label = "wikipedia"
regex = 'https://en\\.wikipedia\\.org/wiki/(\\S+)'
url = "https://en.wikipedia.org/wiki/{match}"
prefix = ""
""")
    with ExitStack() as s:
        mock_execvp = s.enter_context(patch("termbud.zellij.os.execvp"))
        mock_execvp.side_effect = SystemExit(0)
        s.enter_context(patch("termbud.zellij.os.pipe", return_value=(3, 4)))
        s.enter_context(patch("termbud.zellij.os.write"))
        s.enter_context(patch("termbud.zellij.os.close"))
        s.enter_context(patch("termbud.zellij.os.dup2"))
        s.enter_context(patch("termbud.zellij.sys.platform", "darwin"))
        s.enter_context(patch("subprocess.run", side_effect=_dump_screen_side_effect(
            "see https://en.wikipedia.org/wiki/Python_(programming_language)")))
        runner.invoke(app, ["zellij", "pick", "--patterns-file", str(patterns_file)])

    assert mock_execvp.called
    fzf_args = mock_execvp.call_args[0][1]
    assert fzf_args[0] == "fzf"
    assert "--delimiter" in fzf_args
    assert "--with-nth" in fzf_args


def test_pick_no_patterns_found():
    with patch("subprocess.run", side_effect=_dump_screen_side_effect("nothing to match here")):
        result = runner.invoke(app, ["zellij", "pick"])

    assert result.exit_code == 0
    assert "no patterns found" in result.stderr


def test_pick_dump_screen_failure():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "zellij")):
        result = runner.invoke(app, ["zellij", "pick"])

    assert result.exit_code == 1
    assert "failed to dump Zellij screen" in result.stderr


def test_pick_zellij_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = runner.invoke(app, ["zellij", "pick"])

    assert result.exit_code == 1
    assert "failed to dump Zellij screen" in result.stderr


def _invoke_pick(scrollback: str, platform: str, env: dict | None = None, which=MagicMock(return_value="found")):
    with ExitStack() as s:
        mock_execvp = s.enter_context(patch("termbud.zellij.os.execvp"))
        mock_execvp.side_effect = SystemExit(0)
        s.enter_context(patch("termbud.zellij.os.pipe", return_value=(3, 4)))
        mock_write = s.enter_context(patch("termbud.zellij.os.write"))
        s.enter_context(patch("termbud.zellij.os.close"))
        s.enter_context(patch("termbud.zellij.os.dup2"))
        s.enter_context(patch("termbud.zellij.sys.platform", platform))
        s.enter_context(patch("termbud.zellij.os.uname", return_value=MagicMock(release="6.1.0-generic")))
        s.enter_context(patch("termbud.zellij.os.environ", env or {}))
        s.enter_context(patch("termbud.zellij.shutil.which", which))
        s.enter_context(patch("subprocess.run", side_effect=_dump_screen_side_effect(scrollback)))
        runner.invoke(app, ["zellij", "pick"])
    return mock_execvp, mock_write


def test_pick_binds_macos_open_and_pbcopy():
    mock_execvp, _ = _invoke_pick("https://en.wikipedia.org/wiki/Zellij", "darwin")
    fzf_args = mock_execvp.call_args[0][1]
    assert any("open {2}" in a for a in fzf_args)
    assert any("pbcopy" in a for a in fzf_args)


def test_pick_binds_linux_wayland():
    mock_execvp, _ = _invoke_pick(
        "https://en.wikipedia.org/wiki/Wayland_(protocol)", "linux",
        env={"WAYLAND_DISPLAY": "wayland-0"},
    )
    fzf_args = mock_execvp.call_args[0][1]
    assert any("xdg-open {2}" in a for a in fzf_args)
    assert any("wl-copy" in a for a in fzf_args)


def test_pick_binds_linux_x11():
    mock_execvp, _ = _invoke_pick(
        "https://en.wikipedia.org/wiki/X_Window_System", "linux",
        which=MagicMock(return_value=None),
    )
    fzf_args = mock_execvp.call_args[0][1]
    assert any("xclip -selection clipboard" in a for a in fzf_args)


def test_pick_fzf_stdin_tab_separated():
    _, mock_write = _invoke_pick("https://en.wikipedia.org/wiki/Fzf", "darwin")
    written = mock_write.call_args[0][1].decode()
    assert "[url" in written
    assert "wikipedia.org" in written
    assert written.count("\t") >= 2  # display \t url \t yank_value
