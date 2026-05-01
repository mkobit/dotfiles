import pytest
from pathlib import Path

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as a system integration test.")

@pytest.fixture(scope="session")
def chezmoi_source_root():
    """Return the absolute path to the chezmoi source directory (src/chezmoi)."""
    return Path(__file__).parent.parent.parent / "src" / "chezmoi"

@pytest.fixture(scope="session")
def chezmoi_dest(host):
    """Return the absolute path to the chezmoi destination (usually $HOME)."""
    # Use chezmoi to find the target path definitively
    result = host.run("chezmoi target-path")
    if result.rc == 0:
        return Path(result.stdout.strip())
    # Fallback to host home if chezmoi fails
    return Path(host.user().home)

def pytest_generate_tests(metafunc):
    """Dynamically parameterize tests that require layout_name."""
    if "layout_name" in metafunc.fixturenames:
        # We need to find the layouts during collection
        source_root = Path(__file__).parent.parent.parent / "src" / "chezmoi"
        layout_dir = source_root / "dot_config" / "zellij" / "layouts"
        
        layouts = []
        if layout_dir.exists():
            layouts = [p.name.removesuffix(".kdl.tmpl") for p in layout_dir.glob("*.kdl.tmpl")]
        
        metafunc.parametrize("layout_name", layouts)
