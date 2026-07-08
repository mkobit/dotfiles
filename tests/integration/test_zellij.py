import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_zellij_available(host, shell_cmd):
    """Verify zellij binary is on PATH in login shells."""
    result = host.run(f"{shell_cmd} 'command -v zellij'")
    assert result.rc == 0, f"'zellij' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_zellij_version(host, shell_cmd):
    """Verify zellij reports a version string in login shells."""
    result = host.run(f"{shell_cmd} 'zellij --version'")
    assert result.rc == 0, f"'zellij --version' failed via {shell_cmd!r}.\nstderr: {result.stderr}"
    assert "zellij" in result.stdout.lower(), f"Unexpected output from zellij --version: {result.stdout!r}"


@pytest.mark.integration
def test_zellij_config_valid(host):
    """Verify zellij accepts the deployed config."""
    result = host.run("zellij setup --check")
    assert result.rc == 0, f"zellij config is invalid.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
def test_zellij_osc7_precmd_registered(host):
    """Verify _zellij_report_cwd is defined and registered in precmd_functions."""
    result = host.run("zsh -i -l -c 'print ${precmd_functions[@]}'")
    assert result.rc == 0, f"zsh -i -l failed.\nstderr: {result.stderr}"
    assert "_zellij_report_cwd" in result.stdout, f"_zellij_report_cwd not in precmd_functions: {result.stdout!r}"


@pytest.mark.integration
def test_zellij_osc7_emits_sequence(host):
    """Verify _zellij_report_cwd emits a valid OSC 7 working-directory sequence."""
    result = host.run("zsh -i -l -c '_zellij_report_cwd'")
    assert result.rc == 0, f"_zellij_report_cwd failed.\nstderr: {result.stderr}"
    assert "\x1b]7;file://" in result.stdout, f"OSC 7 sequence not found in output: {result.stdout!r}"
