import pytest


@pytest.fixture(scope="module", autouse=True)
def skip_if_zellij_missing(host):
    """Skip layout tests if zellij is not installed on the target host."""
    if host.run("command -v zellij").rc != 0:
        pytest.skip("zellij binary not found; skipping layout validation")


@pytest.mark.integration
def test_zellij_layout_valid(host, layout_name, chezmoi_dest):
    """Verify that each deployed Zellij layout is valid."""
    # Check if the layout was actually deployed to the destination.
    # Templates that evaluate to empty are deleted by chezmoi.
    layout_path = chezmoi_dest / ".config" / "zellij" / "layouts" / f"{layout_name}.kdl"
    if not host.file(str(layout_path)).exists:
        pytest.skip(f"Layout '{layout_name}' not deployed in this environment")

    # zellij setup --dump-layout <name> will exit with non-zero if the layout is invalid
    # Note: it returns 0 if the layout doesn't exist, which is why we check exists first.
    result = host.run(f"zellij setup --dump-layout {layout_name}")
    assert result.rc == 0, f"Zellij layout '{layout_name}' is invalid.\nstderr: {result.stderr}"
    assert "layout {" in result.stdout, f"Zellij layout '{layout_name}' dump seems malformed.\nstdout: {result.stdout}"
