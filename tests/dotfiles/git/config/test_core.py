import src.dotfiles.git.config as c
from pathlib import Path

def test_core():
    core = c.Core(
            autocrlf="input",
            editor="vim",
            excludes_file=Path("/tmp/.gitignore"),
            fsmonitor=True,
            eol="auto",
            safecrlf=True,
    )

    assert core.header() == '[core]'
    file_options = core.file_options()
    assert file_options.get('autocrlf') == "input"
    assert file_options.get('editor') == "vim"
    assert file_options.get('excludesFile') == "/tmp/.gitignore"
    assert file_options.get('fsmonitor') == "true"
    assert file_options.get('eol') == "auto"
    assert file_options.get('safecrlf') == "true"
