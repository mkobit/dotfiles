import pytest

@pytest.fixture(scope="module", autouse=True)
def skip_if_zellij_missing(host):
    """Skip layout tests if zellij is not installed on the target host."""
    if host.run("command -v zellij").rc != 0:
        pytest.skip("zellij binary not found; skipping layout validation")

@pytest.mark.integration
def test_zellij_layout_valid(host, layout_name):
    """Verify that each deployed Zellij layout is valid."""
    # zellij setup --dump-layout <name> will exit with non-zero if the layout is invalid
    # It checks the layout in ~/.config/zellij/layouts/ (or chezmoi_dest / .config / ...)
    result = host.run(f"zellij setup --dump-layout {layout_name}")
    assert result.rc == 0, f"Zellij layout '{layout_name}' is invalid.\nstderr: {result.stderr}"
    assert "layout {" in result.stdout, f"Zellij layout '{layout_name}' dump seems malformed.\nstdout: {result.stdout}"
