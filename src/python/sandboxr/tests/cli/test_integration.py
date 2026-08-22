"""CLI integration tests verifying fail-closed on-hold guard."""

from typer.testing import CliRunner

from sandboxr.main import app

runner = CliRunner()


def test_run_fails_closed_when_on_hold():
    result = runner.invoke(app, ["run", "--", "bash"])
    assert result.exit_code == 1
    assert "error: sandboxr is currently on hold" in result.output


def test_shell_fails_closed_when_on_hold():
    result = runner.invoke(app, ["shell"])
    assert result.exit_code == 1
    assert "error: sandboxr is currently on hold" in result.output


def test_doctor_fails_closed_when_on_hold():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "error: sandboxr is currently on hold" in result.output


def test_help_still_displays():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Run commands in an outer bwrap sandbox" in result.output
