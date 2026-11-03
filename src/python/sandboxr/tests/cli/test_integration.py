"""CLI integration tests verifying fail-closed on-hold guard."""

import pytest
from typer.testing import CliRunner

from sandboxr.main import app

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        ["run", "--", "bash"],
        ["shell"],
        ["doctor"],
    ],
)
def test_commands_fail_closed_when_on_hold(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert "error: sandboxr is currently on hold" in result.output


def test_help_still_displays():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Run commands in an outer bwrap sandbox" in result.output
