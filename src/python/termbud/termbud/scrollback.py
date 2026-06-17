import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from termbud.utils import editor_cmd, platform_cmds

app = typer.Typer(
    help=(
        "Extract command output blocks from a terminal scrollback buffer.\n\n"
        "Typical Zellij trigger (bind to a key in config.kdl):\n\n"
        "  zellij action dump-screen --full /tmp/termbud-scrollback.txt\n"
        "  termbud scrollback extract --from-file /tmp/termbud-scrollback.txt -i\n\n"
        "Or pipe from stdin:\n\n"
        "  cat /tmp/termbud-scrollback.txt | termbud scrollback extract -i"
    )
)

_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

_PROMPT_REGEXES = [
    r"^➜\s+~.*$",  # Example starship success prompt
    r"^❯\s+.*$",  # noqa: RUF001
    r"^➜\s+",  # Broad starship prompt
]


def extract_blocks(scrollback: str) -> list[str]:
    """
    Extracts individual command output blocks from the scrollback by splitting
    on shell prompts heuristically.
    """
    lines = _ANSI_ESCAPE.sub("", scrollback).splitlines()
    blocks = []
    current_block = []

    for line in reversed(lines):
        is_prompt = False
        # Very simple heuristic: ends with standard prompt chars or contains them
        # Adjusting the heuristic to better match starship/zsh configs.
        if "➜" in line or "❯" in line or re.match(r"^[^$#]*[$#]\s*$", line.strip()):  # noqa: RUF001  # noqa: RUF001
            is_prompt = True

        if is_prompt:
            if current_block:
                # Add the collected block (reversed back to original order)
                current_block.reverse()
                # Exclude the actual typed command which usually follows the prompt on the same line
                # But since the prompt might be on a separate line (like with `add_newline = true`),
                # we just take the block as is.
                text = "\n".join(current_block).strip()
                if text:
                    blocks.append(text)
                current_block = []
        else:
            current_block.append(line)

    # Re-reverse to chronological order
    blocks.reverse()
    return blocks


@app.command("extract")
def extract(
    from_file: Annotated[
        Path | None,
        typer.Option("--from-file", help="Read scrollback from file"),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Use fzf to pick a block and action"),
    ] = False,
    copy: Annotated[
        bool,
        typer.Option("--copy", "-c", help="Copy the last block to clipboard"),
    ] = False,
    edit: Annotated[
        bool,
        typer.Option("--edit", "-e", help="Open the last block in an editor"),
    ] = False,
) -> None:
    """
    Split scrollback into blocks of output between shell prompts.

    Each block is the stdout/stderr printed between two prompt lines.
    Without flags, prints the most recent block to stdout.
    Use -i to pick any block interactively via fzf (copy, edit, or dump).
    """
    scrollback = from_file.read_text() if from_file else sys.stdin.read()

    if not scrollback.strip():
        raise typer.Exit(0)

    blocks = extract_blocks(scrollback)
    if not blocks:
        print("termbud: no output blocks found between prompts", file=sys.stderr)
        raise typer.Exit(1)

    if interactive:
        # Pass blocks to fzf. We can delimit blocks by a null byte or unique string,
        # but fzf works on lines. We can create a preview layout.

        # Prepare a temp directory with block files
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            for i, block in enumerate(blocks):
                # Reverse index so 0 is the most recent
                idx = len(blocks) - 1 - i
                (td_path / f"block_{idx}.txt").write_text(block)

            # We create an index for fzf
            fzf_input = "\n".join(f"Block {len(blocks) - 1 - i}" for i in range(len(blocks)))

            _, copy_cmd = platform_cmds()
            editor = editor_cmd()

            fzf_cmd = [
                "fzf",
                "--prompt",
                "Pick output block> ",
                "--header",
                f"ctrl-y: copy  ctrl-e: edit in {editor}  enter: dump  esc: quit",
                "--preview",
                f"cat {td}/block_{{2}}.txt",
                f"--bind=ctrl-y:execute-silent(cat {td}/block_{{2}}.txt | {copy_cmd})+abort",
                f"--bind=ctrl-e:execute({editor} {td}/block_{{2}}.txt)+abort",
                "--bind=enter:accept",
            ]

            result = subprocess.run(
                fzf_cmd,
                input=fzf_input,
                text=True,
                stdout=subprocess.PIPE,
                check=False,
            )

            if result.returncode == 0 and result.stdout:
                # User pressed enter, let's dump it
                match = re.search(r"Block (\d+)", result.stdout)
                if match:
                    idx = int(match.group(1))
                    print(blocks[-(idx + 1)])
    else:
        # Default non-interactive: pick the most recent block
        target_block = blocks[-1]

        if copy:
            _, copy_cmd = platform_cmds()
            subprocess.run(copy_cmd.split(), input=target_block, text=True, check=False)
        elif edit:
            editor = editor_cmd()
            with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tf:
                tf.write(target_block)
                tf_path = tf.name
            subprocess.run([editor, tf_path], check=False)
            Path(tf_path).unlink(missing_ok=True)
        else:
            # Just print
            print(target_block)
