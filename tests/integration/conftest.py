import html
import json
import os
import re
import shlex
import subprocess
from collections.abc import Callable, Iterable, Sequence
from functools import cache
from pathlib import Path
from typing import TypedDict, cast

import pytest
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter
from chezmoi_test_data import required_installation_method
from integration_support.chezmoi import chezmoi_argv
from testinfra.host import Host
from testinfra.modules.user import User


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--start-hammerspoon",
        action="store_true",
        help="Start a dedicated Hammerspoon process for the config load check (macOS CI).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: mark test as a system integration test.")
    config.addinivalue_line("markers", "hammerspoon: load the rendered config in Hammerspoon on macOS.")
    config.addinivalue_line(
        "markers",
        "chezmoi_installation(feature, methods): run only when feature installation_method is in methods.",
    )


@pytest.fixture(autouse=True)
def skip_unmatched_chezmoi_installation(request: pytest.FixtureRequest) -> None:
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


def _deployed_chezmoi_argv(*args: str) -> Sequence[str]:
    return chezmoi_argv(
        *args,
        source=Path.cwd(),
        cache=os.environ.get("CHEZMOI_CACHE_DIR") or None,
        config=os.environ.get("CHEZMOI_CONFIG") or None,
        destination=os.environ.get("CHEZMOI_DEST") or None,
    )


def _chezmoi_command(*args: str) -> str:
    return shlex.join(_deployed_chezmoi_argv(*args))


# chezmoi's documented attribute order for regular/create files is
# (encrypted_)?(private_)?(readonly_)?(empty_)?(executable_)?(dot_) — executable_
# doesn't have to lead, so a plain startswith("executable_") misses e.g.
# private_executable_*. https://www.chezmoi.io/reference/source-state-attributes/
_EXECUTABLE_FILE_ATTRS_RE = re.compile(r"^(create_)?(encrypted_|private_|readonly_|empty_)*executable_")


def _is_shellcheck_candidate_file(source_relative: str) -> bool:
    name = Path(source_relative).name
    return name.startswith("modify_") or bool(_EXECUTABLE_FILE_ATTRS_RE.match(name))


class _ShellcheckCandidate(TypedDict):
    sourceAbsolute: str
    sourceRelative: str


def _shellcheck_candidates() -> list[_ShellcheckCandidate]:
    scripts: dict[str, _ShellcheckCandidate] = json.loads(
        subprocess.run(
            _deployed_chezmoi_argv("managed", "--include=scripts", "--format=json", "--path-style=all"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    files: dict[str, _ShellcheckCandidate] = json.loads(
        subprocess.run(
            _deployed_chezmoi_argv("managed", "--include=files", "--format=json", "--path-style=all"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )

    candidates = list(scripts.values())
    candidates.extend(entry for entry in files.values() if _is_shellcheck_candidate_file(entry["sourceRelative"]))

    on_disk = [entry for entry in candidates if Path(entry["sourceAbsolute"]).is_file()]
    return sorted(on_disk, key=lambda entry: entry["sourceRelative"])


@cache
def _chezmoi_source_path(repository: Path) -> Path:
    """Ask chezmoi itself where its source root is (respects .chezmoiroot).
    Pytest always runs from the repo root, so that's the --source to resolve
    against; a plain local subprocess call, not host.run, since this is a
    question about the checkout on this machine, not the deployed target."""
    result = subprocess.run(
        chezmoi_argv("source-path", source=repository),
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


@pytest.fixture(scope="module")
def chezmoi_data(host: Host) -> dict[str, object]:
    """Return rendered chezmoi data from the initialized test environment.
    Module-scoped: the underlying `host` fixture (pytest-testinfra) is itself
    module-scoped, so session scope would raise a ScopeMismatch."""
    result = host.run(_chezmoi_command("data", "--format=json"))
    assert result.rc == 0, f"chezmoi data failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def chezmoi_source_root() -> Path:
    """Return the absolute path to the chezmoi source directory, as resolved by chezmoi itself."""
    return _chezmoi_source_path(Path.cwd())


@pytest.fixture(scope="session")
def repo_root(chezmoi_source_root: Path) -> Path:
    """Return the absolute path to the repository root (src/chezmoi's grandparent)."""
    return chezmoi_source_root.parent.parent


@pytest.fixture(scope="module")
def chezmoi_dest(host: Host) -> Path:
    """Return the absolute path to the chezmoi destination (usually $HOME).
    Module-scoped to match `host`'s scope; see chezmoi_data for why."""
    result = host.run(_chezmoi_command("target-path"))
    if result.rc == 0:
        return Path(result.stdout.strip())
    # Testinfra's dynamic module loader types host.user() as the base Module.
    return Path(cast(User, host.user()).home)


@pytest.fixture
def chezmoi_command() -> Callable[..., str]:
    return _chezmoi_command


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Dynamically parameterize tests that require layout_name, chezmoiscript_path, workflow_path, or shellcheck_candidate."""
    needs_source_root = {"layout_name", "chezmoiscript_path", "workflow_path", "shellcheck_candidate"} & set(
        metafunc.fixturenames
    )
    if not needs_source_root:
        return

    source_root = _chezmoi_source_path(Path.cwd())
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

    if "shellcheck_candidate" in metafunc.fixturenames:
        candidates = _shellcheck_candidates()
        metafunc.parametrize("shellcheck_candidate", candidates, ids=lambda c: c["sourceRelative"])


def _slow_test_summary(reports: Iterable[TestReport]) -> str:
    durations: dict[str, dict[str, float]] = {}
    for report in reports:
        phases = durations.setdefault(report.nodeid, {})
        phases[report.when] = phases.get(report.when, 0.0) + report.duration
    rows = [
        "### Slowest integration tests",
        "",
        "Times include setup, call, and teardown. Shared fixture setup is charged to its first test.",
        "",
        "| Test | Total (s) | Setup (s) | Call (s) | Teardown (s) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    slowest = sorted(durations.items(), key=lambda item: sum(item[1].values()), reverse=True)[:20]
    for nodeid, phases in slowest:
        name = html.escape(nodeid).replace("|", "&#124;").replace("`", "&#96;")
        times = [sum(phases.values()), *(phases.get(phase, 0.0) for phase in ("setup", "call", "teardown"))]
        rows.append(f"| `{name}` | " + " | ".join(f"{duration:.3f}" for duration in times) + " |")
    return "\n".join(rows) + "\n"


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    reports = [
        report for group in terminalreporter.stats.values() for report in group if isinstance(report, TestReport)
    ]
    try:
        with Path(summary_path).open("a") as summary:
            summary.write(_slow_test_summary(reports))
    except OSError as error:
        terminalreporter.write_line(f"Could not write test duration summary: {error}")
