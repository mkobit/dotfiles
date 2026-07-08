import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "package,binary",
    [
        pytest.param(
            "strace",
            "strace",
            marks=pytest.mark.chezmoi_installation("packages.strace", methods={"apt"}),
        ),
        pytest.param(
            "bubblewrap",
            "bwrap",
            marks=pytest.mark.chezmoi_installation("packages.bubblewrap", methods={"apt"}),
        ),
        pytest.param(
            "socat",
            "socat",
            marks=pytest.mark.chezmoi_installation("packages.socat", methods={"apt"}),
        ),
    ],
)
def test_apt_package_available(host, package, binary):
    """Verify that chezmoi-managed apt packages provide their expected binaries on Linux."""
    result = host.run(f"command -v {binary}")
    assert result.rc == 0, f"Binary '{binary}' (from package {package}) not found in PATH.\nstderr: {result.stderr}"
