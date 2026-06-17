import os
import re
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from termbud.utils import editor_cmd, platform_cmds
from termbud.zellij import (
    Match,
    Pattern,
    _extract,
    _fmt,
    _format_lines,
    _fzf_args,
    _load_patterns,
)

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


# --- format lines ---


def test_format_lines_tab_separated():
    matches = [Match("web", "example.com", "https://example.com", "")]
    line = _format_lines(matches)
    assert line.count("\t") >= 2  # display \t url \t yank_value
    assert "web" in line
    assert "example.com" in line


def test_format_lines_url_template_expanded():
    matches = [Match("ticket", "TICK-123", "https://issues.example.com/browse/{match}", "")]
    line = _format_lines(matches)
    assert "https://issues.example.com/browse/TICK-123" in line


def test_format_lines_prefix_in_display_and_yank():
    matches = [Match("shortlink", "docs/setup", "https://links.example.com/{match}", "go/")]
    line = _format_lines(matches)
    assert "go/docs/setup" in line


# --- platform command selection ---


def test_platform_cmds_macos():
    with patch.object(sys, "platform", "darwin"):
        assert platform_cmds() == ("open", "pbcopy")


def test_platform_cmds_wsl():
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(os, "uname", return_value=MagicMock(release="5.15.0-microsoft-standard-WSL2")),
    ):
        assert platform_cmds() == ("wslview", "clip.exe")


def test_platform_cmds_linux_wayland():
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(os, "uname", return_value=MagicMock(release="6.1.0-generic")),
        patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}),
    ):
        assert platform_cmds() == ("xdg-open", "wl-copy")


def test_platform_cmds_linux_x11():
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(os, "uname", return_value=MagicMock(release="6.1.0-generic")),
        patch.dict(os.environ, {"WAYLAND_DISPLAY": ""}),
        patch.object(shutil, "which", return_value=None),
    ):
        assert platform_cmds() == ("xdg-open", "xclip -selection clipboard")


# --- editor command selection ---


def test_editor_cmd_prefers_visual():
    with patch.dict(os.environ, {"VISUAL": "emacs", "EDITOR": "vim"}):
        assert editor_cmd() == "emacs"


def test_editor_cmd_falls_back_to_editor():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": "vim"}):
        assert editor_cmd() == "vim"


def test_editor_cmd_defaults_to_nvim():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": ""}):
        assert editor_cmd() == "nvim"


# --- fzf argument construction ---


def test_fzf_args_open_bind():
    args = _fzf_args("open", "pbcopy", "nvim")
    assert any("ctrl-o" in a and "open {2}" in a for a in args)


def test_fzf_args_copy_bind():
    args = _fzf_args("open", "pbcopy", "nvim")
    assert any("ctrl-y" in a and "pbcopy" in a for a in args)


def test_fzf_args_editor_bind():
    args = _fzf_args("open", "pbcopy", "vim")
    assert any("ctrl-e" in a and "vim" in a for a in args)
