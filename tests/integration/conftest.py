import json
import os
import shlex
from collections.abc import Iterable
from pathlib import Path

import pytest
from chezmoi_test_data import installation_method


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as a system integration test.")
    config.addinivalue_line(
        "markers",
        "chezmoi_installation(feature, methods): run only when feature installation_method is in methods.",
    )


@pytest.fixture(autouse=True)
def skip_unmatched_chezmoi_installation(request):
    marker = request.node.get_closest_marker("chezmoi_installation")
    if marker is None:
        return

    if len(marker.args) != 1 or not isinstance(marker.args[0], str):
        raise ValueError("chezmoi_installation marker requires exactly one feature name argument")

    methods = marker.kwargs.get("methods")
    if not isinstance(methods, Iterable) or isinstance(methods, str):
        raise ValueError("chezmoi_installation marker requires a methods set")

    feature = marker.args[0]
    allowed_methods = frozenset(methods)
    active_method = installation_method(request.getfixturevalue("chezmoi_data"), feature)

    if active_method not in allowed_methods:
        allowed = ", ".join(sorted(allowed_methods))
        pytest.skip(f"{feature}.installation_method is {active_method!r}; expected one of: {allowed}")


def _chezmoi_command(*args):
    command = ["chezmoi"]

    if config_path := os.environ.get("CHEZMOI_CONFIG"):
        command.extend(["--config", config_path])
    if dest := os.environ.get("CHEZMOI_DEST"):
        command.extend(["--destination", dest])

    command.extend(args)
    return " ".join(shlex.quote(part) for part in command)


@pytest.fixture()
def chezmoi_data(host):
    """Return rendered chezmoi data from the initialized test environment."""
    result = host.run(_chezmoi_command("data", "--format=json"))
    assert result.rc == 0, f"chezmoi data failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


@pytest.fixture()
def chezmoi_source_root():
    """Return the absolute path to the chezmoi source directory (src/chezmoi)."""
    return Path(__file__).parent.parent.parent / "src" / "chezmoi"


@pytest.fixture()
def chezmoi_dest(host):
    """Return the absolute path to the chezmoi destination (usually $HOME)."""
    result = host.run(_chezmoi_command("target-path"))
    if result.rc == 0:
        return Path(result.stdout.strip())
    return Path(host.user().home)


def pytest_generate_tests(metafunc):
    """Dynamically parameterize tests that require layout_name."""
    if "layout_name" in metafunc.fixturenames:
        source_root = Path(__file__).parent.parent.parent / "src" / "chezmoi"
        layout_dir = source_root / "dot_config" / "zellij" / "layouts"

        layouts = []
        if layout_dir.exists():
            layouts = [p.name.removesuffix(".kdl.tmpl") for p in layout_dir.glob("*.kdl.tmpl")]

        metafunc.parametrize("layout_name", layouts)
