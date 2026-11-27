import json
import os
import re
import tempfile
from collections.abc import Callable, Iterable, Sequence
from functools import cache
from heapq import nlargest
from html import escape
from pathlib import Path
from typing import TypedDict, cast

import pytest
from chezmoi_test_data import required_installation_method
from testinfra.host import Host
from testinfra.modules.user import User

from chezmoi_cli import ChezmoiCli, ChezmoiSubcommand, Data, RawCommand, TargetPath


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: mark test as a system integration test.")
    config.addinivalue_line(
        "markers",
        "chezmoi_installation(feature, methods): run only when feature installation_method is in methods.",
    )
    if not hasattr(config, "workerinput") and config.getoption("numprocesses", default=None):
        cache_path = Path(tempfile.gettempdir()) / f"dotfiles-shellcheck-candidates-{os.getpid()}.json"
        _write_shellcheck_cache(cache_path, _compute_shellcheck_candidates())
        os.environ["_DOTFILES_SHELLCHECK_CACHE"] = str(cache_path)


def pytest_unconfigure(config: pytest.Config) -> None:
    if not hasattr(config, "workerinput"):
        cache_file = os.environ.pop("_DOTFILES_SHELLCHECK_CACHE", None)
        if cache_file is not None:
            Path(cache_file).unlink(missing_ok=True)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if getattr(config, "workerinput", None) is None or not config.getvalue("loadgroup"):
        return
    # Work around pytest 9.2 + pytest-xdist 3.8: xdist sets item._nodeid,
    # whereas pytest 9.2's Item.nodeid property reads str(item._id).
    from _pytest.nodes import coerce_node_id  # noqa: PLC0415

    for item in items:
        legacy_nodeid = getattr(item, "_nodeid", None)
        if isinstance(legacy_nodeid, str) and legacy_nodeid != item.nodeid:
            item._id = coerce_node_id(legacy_nodeid)


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    runner = os.environ.get("INTEGRATION_SUMMARY_RUNNER")
    limit = terminalreporter.config.getoption("durations")
    if summary is None or runner is None or not limit:
        return

    reports = (
        report
        for group in terminalreporter.stats.values()
        for report in group
        if isinstance(report, pytest.TestReport) and not report.skipped
    )
    slowest = nlargest(limit, reports, key=lambda report: report.duration)
    if not slowest:
        return

    with Path(summary).open("a", encoding="utf-8") as output:
        output.write(f"\n### Slowest integration test phases ({runner})\n\n")
        output.write("| Test | Phase | Duration (s) |\n| --- | --- | ---: |\n")
        for report in slowest:
            test = escape(" ".join(report.nodeid.splitlines())).replace("|", "&#124;")
            output.write(f"| <code>{test}</code> | {report.when} | {report.duration:.3f} |\n")


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


def _deployed_chezmoi() -> ChezmoiCli:
    return ChezmoiCli(
        source=Path.cwd(),
        cache=os.environ.get("CHEZMOI_CACHE_DIR") or None,
        config=os.environ.get("CHEZMOI_CONFIG") or None,
        destination=os.environ.get("CHEZMOI_DEST") or None,
    )


def _deployed_chezmoi_argv(*args: str) -> Sequence[str]:
    return list(_deployed_chezmoi().raw(*args).argv)


def _chezmoi_command(*args: str, subcommand: ChezmoiSubcommand | None = None) -> str:
    cli = _deployed_chezmoi()
    return cli.command(subcommand if subcommand is not None else RawCommand(args=args)).shell


# chezmoi's documented attribute order for regular/create files is
# (encrypted_)?(private_)?(readonly_)?(empty_)?(executable_)?(dot_) — executable_
# doesn't have to lead, so a plain startswith("executable_") misses e.g.
# private_executable_*. https://www.chezmoi.io/reference/source-state-attributes/
_EXECUTABLE_FILE_ATTRS_RE = re.compile(r"^(create_)?(encrypted_|private_|readonly_|empty_)*executable_")


def _is_shellcheck_candidate_file(source_relative: str) -> bool:
    name = Path(source_relative).name
    return name.startswith("modify_") or bool(_EXECUTABLE_FILE_ATTRS_RE.match(name))


def _is_shellcheck_candidate_entry(source_relative: str) -> bool:
    name = Path(source_relative).name
    return name.startswith("run_") or _is_shellcheck_candidate_file(source_relative)


class _ShellcheckCandidate(TypedDict):
    sourceAbsolute: str
    sourceRelative: str


def _compute_shellcheck_candidates() -> list[_ShellcheckCandidate]:
    cli = _deployed_chezmoi()
    entries: dict[str, _ShellcheckCandidate] = json.loads(
        cli.managed(include=("scripts", "files"), exclude="externals", format="json", path_style="all")
        .run(check=True)
        .stdout
    )

    on_disk = [
        entry
        for entry in entries.values()
        if _is_shellcheck_candidate_entry(entry["sourceRelative"]) and Path(entry["sourceAbsolute"]).is_file()
    ]
    return sorted(on_disk, key=lambda entry: entry["sourceRelative"])


def _write_shellcheck_cache(cache_path: Path, candidates: list[_ShellcheckCandidate]) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=cache_path.parent, prefix=f".{cache_path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(candidates, output)
        os.replace(tmp_name, cache_path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


@cache
def _shellcheck_candidates() -> list[_ShellcheckCandidate]:
    cache_file = os.environ.get("_DOTFILES_SHELLCHECK_CACHE")
    if cache_file is not None:
        cache_path = Path(cache_file)
        if cache_path.is_file():
            return cast(list[_ShellcheckCandidate], json.loads(cache_path.read_text(encoding="utf-8")))
    return _compute_shellcheck_candidates()


@cache
def _chezmoi_source_path(repository: Path) -> Path:
    """Ask chezmoi itself where its source root is (respects .chezmoiroot).
    Pytest always runs from the repo root, so that's the --source to resolve
    against; a plain local subprocess call, not host.run, since this is a
    question about the checkout on this machine, not the deployed target."""
    result = ChezmoiCli(source=repository).source_path().run(check=True)
    return Path(result.stdout.strip())


@pytest.fixture(scope="module")
def chezmoi_data(host: Host) -> dict[str, object]:
    """Return rendered chezmoi data from the initialized test environment.
    Module-scoped: the underlying `host` fixture (pytest-testinfra) is itself
    module-scoped, so session scope would raise a ScopeMismatch."""
    result = host.run(_chezmoi_command(subcommand=Data(format="json")))
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
    result = host.run(_chezmoi_command(subcommand=TargetPath()))
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
            layouts = sorted(p.name.removesuffix(".kdl.tmpl") for p in layout_dir.glob("*.kdl.tmpl"))
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
