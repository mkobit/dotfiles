import os
import re
import shutil
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from termbud.main import app
from termbud.zellij import Match, Pattern, _extract, _fmt, _load_patterns

runner = CliRunner()

# Generic sample text — no relation to any specific org or product.
SAMPLE_SCROLLBACK = """
See https://en.wikipedia.org/wiki/Python_(programming_language) for info.
Also https://en.wikipedia.org/wiki/Zellij and https://fzf.netlify.app/docs.
Join #announcements or #help-desk in chat.
Ticket ref: DOC-00001A2B3C4D5E6F7 assigned to alice.
Internal link: go/onboarding or go/docs/setup.
Config at /etc/hosts and source in ~/projects/myapp/main.py.
"""

TICKET_PATTERN: Pattern = {
    "label": "ticket",
    "regex": r"\b(DOC-[0-9A-F]{17})\b",
    "url": "https://issues.example.com/browse/{match}",
    "prefix": "",
}
CHAT_PATTERN: Pattern = {
    "label": "chat channel",
    "regex": r"#([\w][\w-]+)",
    "url": "https://chat.example.com/channels/{match}",
    "prefix": "#",
}
SHORTLINK_PATTERN: Pattern = {
    "label": "shortlink",
    "regex": r"\bgo/([\w/][\w/-]*)",
    "url": "https://links.example.com/{match}",
    "prefix": "go/",
}
BUILTIN_WEB_PATTERN: Pattern = {
    "label": "web",
    "regex": r'https?://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
    "url": "{match}",
    "prefix": "",
}
BUILTIN_URL_PATTERN: Pattern = {
    "label": "url",
    "regex": r'(?<!\w)(?!https?://)[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
    "url": "{match}",
    "prefix": "",
}
BUILTIN_PATH_PATTERN: Pattern = {
    "label": "path",
    "regex": r'(?<![/:\w])((?:~|\.{1,2})?/[^\s<>"\',:;`|&\\]+)',
    "url": "{match}",
    "prefix": "",
}


# --- extraction helpers ---


def test_extract_web_url():
    text = "visit https://en.wikipedia.org/wiki/Main_Page today"
    matches = _extract(text, [BUILTIN_WEB_PATTERN])
    assert matches == [Match("web", "https://en.wikipedia.org/wiki/Main_Page", "{match}", "")]


def test_extract_url_non_https_protocol():
    matches = _extract("clone ftp://files.example.com/archive.tar.gz done", [BUILTIN_URL_PATTERN])
    assert len(matches) == 1
    assert matches[0].label == "url"
    assert matches[0].value.startswith("ftp://")


def test_extract_url_file_protocol():
    matches = _extract("open file:///home/user/notes.txt here", [BUILTIN_URL_PATTERN])
    assert len(matches) == 1
    assert matches[0].label == "url"
    assert matches[0].value == "file:///home/user/notes.txt"


def test_extract_https_not_matched_by_url_pattern():
    matches = _extract("see https://example.com for info", [BUILTIN_URL_PATTERN])
    assert len(matches) == 0


def test_extract_absolute_path():
    matches = _extract("config at /etc/hosts and /usr/local/bin/python", [BUILTIN_PATH_PATTERN])
    values = [m.value for m in matches]
    assert "/etc/hosts" in values
    assert "/usr/local/bin/python" in values


def test_extract_home_path():
    matches = _extract("edit ~/projects/myapp/main.py now", [BUILTIN_PATH_PATTERN])
    assert len(matches) == 1
    assert matches[0].value == "~/projects/myapp/main.py"


def test_extract_path_does_not_match_inside_url():
    # /wiki/Main_Page is part of a URL — path pattern should not extract it separately.
    text = "see https://en.wikipedia.org/wiki/Main_Page for details"
    matches = _extract(text, [BUILTIN_PATH_PATTERN])
    assert not any("/wiki/Main_Page" in m.value for m in matches)


def test_extract_custom_pattern():
    matches = _extract("ref DOC-00001A2B3C4D5E6F7 open", [TICKET_PATTERN])
    assert len(matches) == 1
    assert matches[0].label == "ticket"
    assert matches[0].value == "DOC-00001A2B3C4D5E6F7"


def test_extract_prefix_pattern_strips_prefix():
    matches = _extract("join #help-desk now", [CHAT_PATTERN])
    assert matches[0].value == "help-desk"


def test_extract_deduplicates():
    matches = _extract("go/docs go/docs again", [SHORTLINK_PATTERN])
    assert len(matches) == 1


def test_extract_multiple_patterns():
    matches = _extract(SAMPLE_SCROLLBACK, [BUILTIN_WEB_PATTERN, TICKET_PATTERN, CHAT_PATTERN, SHORTLINK_PATTERN])
    labels = [m.label for m in matches]
    assert "web" in labels
    assert "ticket" in labels
    assert "chat channel" in labels
    assert "shortlink" in labels


def test_fmt_label_and_display_present():
    line = _fmt("ticket", "DOC-00001A2B3C4D5E6F7")
    assert "ticket" in line
    assert "DOC-00001A2B3C4D5E6F7" in line


def test_fmt_label_padded_to_width():
    label_width = 12
    line = _fmt("web", "https://example.com", label_width=label_width)
    plain = re.sub(r"\033\[[0-9;]*m", "", line)
    assert plain[:label_width] == f"{'web':>{label_width}}"
    assert "https://example.com" in plain


def test_load_patterns_missing_file():
    assert _load_patterns(Path("/nonexistent/patterns.toml")) == []


def test_load_patterns_none():
    assert _load_patterns(None) == []


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


def _invoke_pick(scrollback: str, platform: str, env: dict | None = None, which: MagicMock | None = None):
    with ExitStack() as s:
        mock_run = s.enter_context(patch.object(subprocess, "run", return_value=MagicMock()))
        s.enter_context(patch.object(sys, "platform", platform))
        s.enter_context(patch.object(os, "uname", return_value=MagicMock(release="6.1.0-generic")))
        s.enter_context(patch.dict(os.environ, env or {}, clear=True))
        s.enter_context(patch.object(shutil, "which", which or MagicMock(return_value="found")))
        runner.invoke(app, ["zellij", "pick"], input=scrollback)
    return mock_run


def _fzf_call_args(mock_run) -> list[str]:
    for c in mock_run.call_args_list:
        if c[0][0][0] == "fzf":
            return c[0][0]
    return []


def test_pick_execs_fzf(tmp_path):
    patterns_file = tmp_path / "patterns.toml"
    patterns_file.write_text("""
[patterns.wiki]
label = "wikipedia"
regex = 'https://en\\.wikipedia\\.org/wiki/(\\S+)'
url = "https://en.wikipedia.org/wiki/{match}"
prefix = ""
""")
    with patch.object(subprocess, "run", return_value=MagicMock()), patch.object(sys, "platform", "darwin"):
        runner.invoke(
            app,
            ["zellij", "pick", "--patterns-file", str(patterns_file)],
            input="see https://en.wikipedia.org/wiki/Python_(programming_language)",
        )


def test_pick_no_patterns_found():
    with patch.object(subprocess, "run", return_value=MagicMock()):
        result = runner.invoke(app, ["zellij", "pick"], input="nothing to match here !!!")

    assert result.exit_code == 0
    assert "no patterns found" in result.stderr


def test_pick_binds_macos_open_and_pbcopy():
    mock_run = _invoke_pick("https://en.wikipedia.org/wiki/Zellij", "darwin")
    args = _fzf_call_args(mock_run)
    assert any("open {2}" in a for a in args)
    assert any("pbcopy" in a for a in args)


def test_pick_binds_linux_wayland():
    mock_run = _invoke_pick(
        "https://en.wikipedia.org/wiki/Wayland_(protocol)",
        "linux",
        env={"WAYLAND_DISPLAY": "wayland-0"},
    )
    args = _fzf_call_args(mock_run)
    assert any("xdg-open {2}" in a for a in args)
    assert any("wl-copy" in a for a in args)


def test_pick_binds_linux_x11():
    mock_run = _invoke_pick(
        "https://en.wikipedia.org/wiki/X_Window_System",
        "linux",
        which=MagicMock(return_value=None),
    )
    args = _fzf_call_args(mock_run)
    assert any("xclip -selection clipboard" in a for a in args)


def test_pick_binds_ctrl_e_editor():
    mock_run = _invoke_pick("https://en.wikipedia.org/wiki/Vim", "darwin", env={"EDITOR": "vim"})
    args = _fzf_call_args(mock_run)
    assert any("ctrl-e" in a and "vim" in a for a in args)


def test_pick_ctrl_e_defaults_to_nvim():
    mock_run = _invoke_pick("/etc/hosts", "darwin", env={})
    args = _fzf_call_args(mock_run)
    assert any("ctrl-e" in a and "nvim" in a for a in args)


def test_pick_fzf_input_tab_separated():
    mock_run = _invoke_pick("https://en.wikipedia.org/wiki/Fzf", "darwin")
    fzf_call = next(c for c in mock_run.call_args_list if c[0][0][0] == "fzf")
    fzf_input = fzf_call[1]["input"]
    assert "web" in fzf_input
    assert "wikipedia.org" in fzf_input
    assert fzf_input.count("\t") >= 2  # display \t url \t yank_value
