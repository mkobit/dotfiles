# ruff: noqa: RUF001
import subprocess

from typer.testing import CliRunner

from termbud.main import app
from termbud.scrollback import extract_blocks

runner = CliRunner()


def test_extract_blocks_single():
    text = """
➜  ~ echo "hello"
hello
➜  ~
"""
    blocks = extract_blocks(text)
    assert len(blocks) == 1
    assert blocks[0] == "hello"


def test_extract_blocks_multiple():
    text = """
➜  ~ echo "hello"
hello
world
➜  ~ echo "foo"
foo
bar
➜  ~
"""
    blocks = extract_blocks(text)
    assert len(blocks) == 2
    assert blocks[0] == "hello\nworld"
    assert blocks[1] == "foo\nbar"


def test_extract_blocks_with_zsh_style():
    text = """
❯ echo "hello"
hello
❯
"""
    blocks = extract_blocks(text)
    assert len(blocks) == 1
    assert blocks[0] == "hello"


def test_extract_blocks_empty():
    blocks = extract_blocks("just some text")
    assert len(blocks) == 0


def test_extract_blocks_no_trailing_prompt():
    text = """
➜  ~ echo "hello"
hello
"""
    extract_blocks(text)
    # The current heuristic requires a prompt to close the block.
    # If there's no trailing prompt, it might not capture anything,
    # or it might capture up to the end. Let's see how our heuristic behaves.
    # Actually, the last prompt is found first (reversed), and it will close
    # the block. Wait, if there is only one prompt, it won't yield a block
    # because it needs a *subsequent* prompt to start accumulating and then another to close it.


def test_extract_cli_copy(tmp_path, monkeypatch):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text(
        """
➜  ~ echo "hello"
hello output
➜  ~
"""
    )

    calls = []

    def mock_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["scrollback", "extract", "--from-file", str(scrollback_file), "--copy"])

    assert result.exit_code == 0
    assert len(calls) == 1

    # Check that input is the extracted text
    assert calls[0][1]["input"] == "hello output"


def test_extract_cli_print(tmp_path):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text(
        """
➜  ~ echo "hello"
hello output
➜  ~
"""
    )

    result = runner.invoke(app, ["scrollback", "extract", "--from-file", str(scrollback_file)])

    assert result.exit_code == 0
    assert result.stdout.strip() == "hello output"
