"""sandboxr: run commands and agents inside an outer sandbox.

HITL mode: run agent CLIs directly (claude, agy, opencode) — the tool's
own permission prompts are the UX boundary. Nothing here applies.

Autonomous mode: sandboxr run -- TOOL ARGS — the OS sandbox enforces
the security boundary; the tool's own permission prompts are bypassed.
"""

import sys

import typer

from sandboxr.cli.doctor import doctor
from sandboxr.cli.profiles import profiles
from sandboxr.cli.run import run
from sandboxr.cli.shell import shell

app = typer.Typer(
    help="Run commands in an outer sandbox per ~/.config/ai-policy/sandbox.toml.",
    no_args_is_help=True,
)

_RUN_CTX = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}

app.command(context_settings=_RUN_CTX)(run)
app.command(context_settings=_RUN_CTX)(shell)
app.command()(doctor)
app.command()(profiles)


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())
