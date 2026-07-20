import json
import os
import shlex
import subprocess
from collections.abc import Iterable
from pathlib import Path

import pytest
from chezmoi_test_data import required_installation_method


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
    active_method = required_installation_method(request.getfixturevalue("chezmoi_data"), feature)

    if active_method not in allowed_methods:
        allowed = ", ".join(sorted(allowed_methods))
        pytest.skip(f"{feature}.installation_method is {active_method!r}; expected one of: {allowed}")


def _chezmoi_argv(*args):
    command = ["chezmoi"]

    if config_path := os.environ.get("CHEZMOI_CONFIG"):
        command.extend(["--config", config_path])
    if dest := os.environ.get("CHEZMOI_DEST"):
        command.extend(["--destination", dest])

    command.extend(args)
    return command


def _chezmoi_command(*args):
    return " ".join(shlex.quote(part) for part in _chezmoi_argv(*args))


def _chezmoi_source_path():
    """Ask chezmoi itself where its source root is (respects .chezmoiroot).
    Pytest always runs from the repo root, so that's the --source to resolve
    against; a plain local subprocess call, not host.run, since this is a
    question about the checkout on this machine, not the deployed target."""
    result = subprocess.run(
        ["chezmoi", "--source", str(Path.cwd()), "source-path"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


@pytest.fixture()
def chezmoi_data(host):
    """Return rendered chezmoi data from the initialized test environment."""
    result = host.run(_chezmoi_command("data", "--format=json"))
    assert result.rc == 0, f"chezmoi data failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


@pytest.fixture()
def chezmoi_source_root():
    """Return the absolute path to the chezmoi source directory, as resolved by chezmoi itself."""
    return _chezmoi_source_path()


@pytest.fixture()
def repo_root(chezmoi_source_root):
    """Return the absolute path to the repository root (src/chezmoi's grandparent)."""
    return chezmoi_source_root.parent.parent


@pytest.fixture()
def chezmoi_dest(host):
    """Return the absolute path to the chezmoi destination (usually $HOME)."""
    result = host.run(_chezmoi_command("target-path"))
    if result.rc == 0:
        return Path(result.stdout.strip())
    return Path(host.user().home)


def pytest_generate_tests(metafunc):
    """Dynamically parameterize tests that require layout_name, chezmoiscript_path, or workflow_path."""
    needs_source_root = {"layout_name", "chezmoiscript_path", "workflow_path"} & set(metafunc.fixturenames)
    if not needs_source_root:
        return

    source_root = _chezmoi_source_path()
    repo_root = source_root.parent.parent

    if "layout_name" in metafunc.fixturenames:
        layout_dir = source_root / "dot_config" / "zellij" / "layouts"
        layouts = []
        if layout_dir.exists():
            layouts = [p.name.removesuffix(".kdl.tmpl") for p in layout_dir.glob("*.kdl.tmpl")]
        metafunc.parametrize("layout_name", layouts)

    if "chezmoiscript_path" in metafunc.fixturenames:
        scripts = sorted((source_root / ".chezmoiscripts").glob("run_onchange_after_*.sh.tmpl"))
        metafunc.parametrize("chezmoiscript_path", scripts, ids=lambda p: p.name)

    if "workflow_path" in metafunc.fixturenames:
        workflows = sorted((repo_root / ".github" / "workflows").glob("*.yml"))
        metafunc.parametrize("workflow_path", workflows, ids=lambda p: p.name)
