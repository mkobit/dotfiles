import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "package,binary",
    [
        ("strace", "strace"),
        ("bubblewrap", "bwrap"),
        ("socat", "socat"),
    ],
)
def test_apt_package_available(host, package, binary):
    """Verify that chezmoi-managed apt packages provide their expected binaries on Linux."""
    if host.system_info.type == "darwin":
        pytest.skip("Apt packages are not installed on macOS")

    result = host.run(f"command -v {binary}")
    assert result.rc == 0, f"Binary '{binary}' (from package {package}) not found in PATH.\nstderr: {result.stderr}"
