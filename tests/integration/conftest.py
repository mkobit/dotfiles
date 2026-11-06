import json
import os
import re
import shlex
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pytest
from chezmoi_test_data import required_installation_method

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles")
_AGENT_SOURCE_FILES = (
    Path(".chezmoitemplates/python/filter-interpreter"),
    Path(".chezmoidata/ai/plugin-bridge.toml"),
    _BUNDLE / "plugin.json.tmpl",
    *(_BUNDLE / host / f"dot_{host}-plugin/plugin.json.tmpl" for host in ("claude", "codex", "cursor")),
    Path("dot_cursor/plugins/local/mkobit-dotfiles/exact_dot_cursor-plugin/plugin.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
)


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
    command = ["chezmoi", "--source", str(Path.cwd())]

    if cache_dir := os.environ.get("CHEZMOI_CACHE_DIR"):
        command.extend(["--cache", cache_dir])
    if config_path := os.environ.get("CHEZMOI_CONFIG"):
        command.extend(["--config", config_path])
    if dest := os.environ.get("CHEZMOI_DEST"):
        command.extend(["--destination", dest])

    command.extend(args)
    return command


def _chezmoi_command(*args):
    return " ".join(shlex.quote(part) for part in _chezmoi_argv(*args))


# chezmoi's documented attribute order for regular/create files is
# (encrypted_)?(private_)?(readonly_)?(empty_)?(executable_)?(dot_) — executable_
# doesn't have to lead, so a plain startswith("executable_") misses e.g.
# private_executable_*. https://www.chezmoi.io/reference/source-state-attributes/
_EXECUTABLE_FILE_ATTRS_RE = re.compile(r"^(create_)?(encrypted_|private_|readonly_|empty_)*executable_")


def _is_shellcheck_candidate_file(source_relative):
    name = Path(source_relative).name
    return name.startswith("modify_") or bool(_EXECUTABLE_FILE_ATTRS_RE.match(name))


def _shellcheck_candidates():
    scripts = json.loads(
        subprocess.run(
            _chezmoi_argv("managed", "--include=scripts", "--format=json", "--path-style=all"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    files = json.loads(
        subprocess.run(
            _chezmoi_argv("managed", "--include=files", "--format=json", "--path-style=all"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )

    candidates = list(scripts.values())
    candidates.extend(entry for entry in files.values() if _is_shellcheck_candidate_file(entry["sourceRelative"]))

    on_disk = [entry for entry in candidates if Path(entry["sourceAbsolute"]).is_file()]
    return sorted(on_disk, key=lambda entry: entry["sourceRelative"])


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


@pytest.fixture(scope="module")
def chezmoi_data(host):
    """Return rendered chezmoi data from the initialized test environment.
    Module-scoped: the underlying `host` fixture (pytest-testinfra) is itself
    module-scoped, so session scope would raise a ScopeMismatch."""
    result = host.run(_chezmoi_command("data", "--format=json"))
    assert result.rc == 0, f"chezmoi data failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def chezmoi_source_root():
    """Return the absolute path to the chezmoi source directory, as resolved by chezmoi itself."""
    return _chezmoi_source_path()


@pytest.fixture(scope="session")
def repo_root(chezmoi_source_root):
    """Return the absolute path to the repository root (src/chezmoi's grandparent)."""
    return chezmoi_source_root.parent.parent


@pytest.fixture(scope="module")
def chezmoi_dest(host):
    """Return the absolute path to the chezmoi destination (usually $HOME).
    Module-scoped to match `host`'s scope; see chezmoi_data for why."""
    result = host.run(_chezmoi_command("target-path"))
    if result.rc == 0:
        return Path(result.stdout.strip())
    return Path(host.user().home)


@pytest.fixture
def chezmoi_command():
    return _chezmoi_command


def pytest_generate_tests(metafunc):
    """Dynamically parameterize tests that require layout_name, chezmoiscript_path, workflow_path, or shellcheck_candidate."""
    needs_source_root = {"layout_name", "chezmoiscript_path", "workflow_path", "shellcheck_candidate"} & set(
        metafunc.fixturenames
    )
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

    if "shellcheck_candidate" in metafunc.fixturenames:
        candidates = _shellcheck_candidates()
        metafunc.parametrize("shellcheck_candidate", candidates, ids=lambda c: c["sourceRelative"])


@dataclass(frozen=True)
class AgentSourceFixture:
    """An isolated base-like checkout whose config runs the real preparation hook."""

    repo: Path
    source: Path
    authored: Path
    destination: Path
    config: Path
    state: Path
    cache: Path

    @classmethod
    def create(cls, root: Path) -> AgentSourceFixture:
        """Build ``root/repo`` with the real agent source templates, launcher, and module."""
        repo = root / "repo"
        source = repo / "src/chezmoi"
        origin = _REPOSITORY_ROOT / "src/chezmoi"
        shutil.copytree(origin / ".chezmoitemplates/ai", source / ".chezmoitemplates/ai")
        for relative in _AGENT_SOURCE_FILES:
            (source / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin / relative, source / relative)
        python_origin = _REPOSITORY_ROOT / "src/python/skill_filter"
        python_target = repo / "src/python/skill_filter"
        (python_target / "skill_filter").mkdir(parents=True)
        for name in ("prepare-agent-sources.sh", "resolve-interpreter.sh"):
            shutil.copy2(python_origin / name, python_target / name)
        for module in (python_origin / "skill_filter").glob("*.py"):
            shutil.copy2(module, python_target / "skill_filter" / module.name)
        (repo / "src/ai/skills").mkdir(parents=True)
        (repo / ".chezmoiroot").write_text("src/chezmoi\n", encoding="utf-8")
        subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
        destination = root / "destination"
        destination.mkdir()
        fixture = cls(
            repo=repo,
            source=source,
            authored=repo / "src",
            destination=destination,
            config=root / "chezmoi.toml",
            state=root / "chezmoistate.boltdb",
            cache=root / "cache",
        )
        fixture.write_config()
        return fixture

    @property
    def launcher(self) -> Path:
        return self.repo / "src/python/skill_filter/prepare-agent-sources.sh"

    def write_config(self, data: str = "", *, counter: Path | None = None) -> None:
        """Write the hook as base .chezmoi.toml.tmpl renders it, then extra TOML data.

        With ``counter``, the hook appends one line per run before it runs the launcher.
        """
        arguments = [str(self.source), str(self.destination)]
        if counter is None:
            hook = f"command = {json.dumps(str(self.launcher))}\nargs = {json.dumps(arguments)}\n"
        else:
            script = f'echo once >> {shlex.quote(str(counter))} && exec "$0" "$@"'
            hook = f'command = "sh"\nargs = {json.dumps(["-c", script, str(self.launcher), *arguments])}\n'
        self.config.write_text(
            "[hooks.read-source-state.pre]\n"
            + hook
            + '[data.ai.plugin_bridge]\ndefault_hosts = ["claude", "codex", "cursor"]\n'
            + data,
            encoding="utf-8",
        )

    def write_plugin(
        self,
        directory: str,
        identity: dict | None = None,
        *,
        skills: dict[str, dict[str, str | bytes]] | None = None,
        wrappers: dict[str, dict[str, str | bytes]] | None = None,
    ) -> Path:
        """Write an overlay-like plugin: ``plugin.json``, ``skills/<skill>/...``, and ``wrappers/<host>/...``."""
        root = self.authored / "overlay-plugins" / directory
        root.mkdir(parents=True, exist_ok=True)
        body = {"description": f"{directory} fixture plugin.", **(identity or {})}
        (root / "plugin.json").write_text(json.dumps(body), encoding="utf-8")
        trees = {f"skills/{name}": files for name, files in (skills or {}).items()}
        trees.update({f"wrappers/{host}": files for host, files in (wrappers or {}).items()})
        for prefix, files in trees.items():
            for relative, contents in files.items():
                path = root / prefix / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(contents, bytes):
                    path.write_bytes(contents)
                else:
                    path.write_text(contents, encoding="utf-8")
        return root

    def managed_files(self) -> set[str]:
        result = self.run("managed", "--include=files")
        assert result.returncode == 0, result.stderr
        return set(result.stdout.splitlines())

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "chezmoi",
                "--source",
                str(self.repo),
                "--destination",
                str(self.destination),
                "--config",
                str(self.config),
                "--persistent-state",
                str(self.state),
                "--cache",
                str(self.cache),
                *args,
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )


@pytest.fixture
def agent_source_fixture(tmp_path):
    """Return an isolated base-like checkout whose config runs the real preparation hook."""
    return AgentSourceFixture.create(tmp_path)


@pytest.fixture
def agent_source_factory():
    """Return ``AgentSourceFixture.create`` for tests that need several or optional checkouts."""
    return AgentSourceFixture.create


@pytest.fixture
def checkout_config(tmp_path):
    """Write a config that runs the base preparation hook on this checkout, as base init renders it."""
    source = _REPOSITORY_ROOT / "src/chezmoi"
    launcher = _REPOSITORY_ROOT / "src/python/skill_filter/prepare-agent-sources.sh"
    destination = tmp_path / "checkout-destination"
    destination.mkdir()
    config = tmp_path / "checkout-chezmoi.toml"
    config.write_text(
        "[hooks.read-source-state.pre]\n"
        f"command = {json.dumps(str(launcher))}\n"
        f"args = {json.dumps([str(source), str(destination)])}\n"
        '[data.ai.plugin_bridge]\ndefault_hosts = ["claude", "codex", "cursor"]\n',
        encoding="utf-8",
    )
    return config
