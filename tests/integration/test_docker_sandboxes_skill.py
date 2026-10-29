import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml
from test_ai_skills import (
    AUTHORED_SKILL_ROOTS,
    CAPABILITY_AUTHORED_SKILL_ROOTS,
    _apply_authored_cleanup,
    _initialize_authored_cleanup_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "src" / "ai" / "skills" / "sbx-sandboxes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"
ORCHESTRATOR_DIR = SKILL_DIR.with_name("sbx-orchestrator")
MOVED_REFERENCES = ("subagent-task.md", "nested-execution.md")


def _assert_deployed_skill_trees(destination: Path) -> None:
    for root in AUTHORED_SKILL_ROOTS.values():
        for skill_dir in (SKILL_DIR, ORCHESTRATOR_DIR):
            deployed = destination / root / skill_dir.name
            expected = {
                path.relative_to(skill_dir): path.read_bytes() for path in skill_dir.rglob("*") if path.is_file()
            }
            actual = {path.relative_to(deployed): path.read_bytes() for path in deployed.rglob("*") if path.is_file()}
            assert actual == expected
            assert not any(path.is_symlink() for path in deployed.rglob("*"))
        for name in MOVED_REFERENCES:
            assert not (destination / root / "sbx-sandboxes/references" / name).exists()
            assert (destination / root / "sbx-orchestrator/references" / name).is_file()


@pytest.mark.parametrize(
    "command",
    [
        "sbx --help",
        "sbx help",
        "sbx help env",
        "sbx env --help",
        "sbx env exec --help",
        "sbx env create --help",
        "sbx kit --help",
        "sbx kit verify --help",
        "sbx policy profile --help",
        "sbx ls --format json",
        "sbx diagnose --format json",
        "sbx env exec .sbx/sbxenv.yaml -- find / -name agy",
        "sbx env exec /tmp/project/.sbx/custom.yaml -- bun test",
        "sbx env exec ../other/environment.yaml -- codex exec task",
        "sbx env exec .sbx/base.yaml .sbx/override.yaml -- pytest",
        'sbx env exec "/tmp/project with spaces/environment.yaml" -- bun test',
        "sbx exec routine-flow-agy which agy",
        "sbx exec routine-flow-agy agy --help",
    ],
)
@pytest.mark.parametrize("skill_dir", [SKILL_DIR, ORCHESTRATOR_DIR], ids=["sandboxes", "orchestrator"])
def test_skill_grants_execution_and_discovery(command: str, skill_dir: Path) -> None:
    """Cover discovery and guest execution patterns in the package metadata."""
    metadata = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    patterns = [entry.removeprefix("Bash(").removesuffix(")") for entry in metadata["allowed-tools"]]
    assert any(fnmatch.fnmatchcase(command, pattern) for pattern in patterns)


@pytest.mark.parametrize(
    "command",
    [
        "sbx rm task",
        "sbx reset",
        "sbx kit add task kit",
        "sbx diagnose --upload",
        "sbx diagnose --format json --upload",
        "sbx env create environment.yaml",
    ],
)
@pytest.mark.parametrize("skill_dir", [SKILL_DIR, ORCHESTRATOR_DIR], ids=["sandboxes", "orchestrator"])
def test_skill_does_not_grant_lifecycle_or_upload(command: str, skill_dir: Path) -> None:
    """Keep lifecycle changes and report uploads outside the grants."""
    metadata = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    patterns = [entry.removeprefix("Bash(").removesuffix(")") for entry in metadata["allowed-tools"]]
    assert not any(fnmatch.fnmatchcase(command, pattern) for pattern in patterns)


@pytest.mark.parametrize("installed_old_skill", [False, True], ids=["fresh", "upgrade"])
def test_split_skills_deploy_and_remove_old_copies(tmp_path: Path, installed_old_skill: bool) -> None:
    """Deploy both complete trees and remove retired files without changing other packages."""
    source, destination = tmp_path / "source", tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)
    catalog = tomllib.loads((REPO_ROOT / "src/chezmoi/.chezmoidata/ai/skills/authored.toml").read_text())
    selected = {
        name: catalog["ai"]["skills"]["authored"][name]
        for name in ("docker-sandboxes", "sbx-sandboxes", "sbx-orchestrator")
    }
    assert selected == {"docker-sandboxes": "absent", "sbx-sandboxes": "present", "sbx-orchestrator": "present"}
    for skill_dir in (SKILL_DIR, ORCHESTRATOR_DIR):
        shutil.copytree(skill_dir, source / "src/ai/skills" / skill_dir.name)
    direct_roots = (".claude/skills", ".codex/skills", ".cursor/skills", ".gemini/antigravity-cli/skills")
    for root in (*CAPABILITY_AUTHORED_SKILL_ROOTS.values(), *direct_roots):
        old = destination / root / "docker-sandboxes/SKILL.md"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text("old skill")
    for host in (".claude", ".codex"):
        for package, skill in (
            ("mkobit-dotfiles", "docker-sandboxes"),
            ("mkobit-dotfiles", "other-skill"),
            ("other-plugin", "docker-sandboxes"),
        ):
            cached = destination / host / "plugins/cache/dotfiles" / package / "1.0.0/skills" / skill / "SKILL.md"
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text("cached")
    for target in ("dot_claude", "dot_codex", "dot_cursor", "dot_gemini"):
        (source / "src/chezmoi" / target).mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            REPO_ROOT / "src/chezmoi" / target / ".chezmoiremove.tmpl",
            source / "src/chezmoi" / target / ".chezmoiremove.tmpl",
        )
    config = tmp_path / "chezmoi.toml"

    def write_config(states: dict[str, str]) -> None:
        config.write_text(
            "[data.ai.skills.authored]\n"
            + "".join(f'{name} = "{state}"\n' for name, state in states.items())
            + '\n[data.ai.skills.external]\n[data.ai.agents.external]\n[data.local.bin.agy]\ninstallation_method = "system"\n'
        )

    if installed_old_skill:
        old_references = source / "src/ai/skills/sbx-sandboxes/references"
        for name in MOVED_REFERENCES:
            shutil.copy2(ORCHESTRATOR_DIR / "references" / name, old_references / name)
        write_config({**selected, "sbx-orchestrator": "absent"})
        initial = _apply_authored_cleanup(source, destination, config)
        assert initial.returncode == 0, initial.stderr
        for root in AUTHORED_SKILL_ROOTS.values():
            for name in MOVED_REFERENCES:
                assert (destination / root / "sbx-sandboxes/references" / name).is_file()
        for name in MOVED_REFERENCES:
            (old_references / name).unlink()

    write_config(selected)
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    for root in (*CAPABILITY_AUTHORED_SKILL_ROOTS.values(), *direct_roots):
        assert not (destination / root / "docker-sandboxes").exists()
    for host in (".claude", ".codex"):
        cache = destination / host / "plugins/cache/dotfiles"
        assert not (cache / "mkobit-dotfiles/1.0.0/skills/docker-sandboxes").exists()
        assert (cache / "mkobit-dotfiles/1.0.0/skills/other-skill/SKILL.md").is_file()
        assert (cache / "other-plugin/1.0.0/skills/docker-sandboxes/SKILL.md").is_file()
    _assert_deployed_skill_trees(destination)


@pytest.mark.parametrize("skill_dir", [SKILL_DIR, ORCHESTRATOR_DIR], ids=["sandboxes", "orchestrator"])
def test_skill_local_links_resolve_in_the_deployed_pair(skill_dir: Path) -> None:
    """Resolve reference links within the pair that is copied to each skill root."""
    for document in skill_dir.rglob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (document.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_file(), f"Broken link in {document}: {target}"
            assert resolved.is_relative_to(SKILL_DIR) or resolved.is_relative_to(ORCHESTRATOR_DIR)


@pytest.mark.parametrize("worker_exit_code", [0, 23], ids=["success", "failure"])
@pytest.mark.parametrize("resume", [False, True], ids=["launch", "resume"])
def test_codex_launcher_preserves_guest_arguments_logs_and_exit_code(
    tmp_path: Path, worker_exit_code: int, resume: bool
) -> None:
    """Run the documented shell with fake SBX and Codex processes, not a live sandbox."""
    document = (ORCHESTRATOR_DIR / "references/worker-launch.md").read_text(encoding="utf-8")
    launchers = re.findall(r"```sh\n(.*?)\n```", document, re.DOTALL)
    assert len(launchers) == 2
    tools = tmp_path / "host tools"
    tools.mkdir()
    fake_sbx = tools / "sbx"
    fake_sbx.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        'assert sys.argv[1:7] == ["env", "exec", "--name", os.environ["SBX_SANDBOX_NAME"], '
        'os.environ["SBX_ENVIRONMENT"], "--"]\n'
        'os.environ["SBX_CAPTURED_SANDBOX_NAME"] = sys.argv[4]\n'
        "os.execvpe(sys.argv[7], sys.argv[7:], os.environ)\n"
    )
    fake_sbx.chmod(0o755)
    guest = tmp_path / "guest workspace 'quoted'"
    guest.mkdir()
    executable = guest / "guest codex"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        'Path(os.environ["SBX_CAPTURE"]).write_text(json.dumps({"argv": sys.argv[1:], '
        '"sandbox_name": os.environ["SBX_CAPTURED_SANDBOX_NAME"], '
        '"workdir": str(Path.cwd()), "stdin": sys.stdin.read()}))\n'
        'print("guest stdout")\n'
        'print("guest stderr", file=sys.stderr)\n'
        'sys.exit(int(os.environ["SBX_WORKER_EXIT_CODE"]))\n'
    )
    executable.chmod(0o755)
    capture = tmp_path / "captured.json"
    log = tmp_path / "host log.txt"
    marker = tmp_path / "must-not-exist"
    prompt = f"Keep 'quotes', \"double quotes\", $variables, and newlines.\n$(touch {marker}); exit 91"
    model = "model 'literal' $variable"
    session_id = f"session 'literal' $(touch {marker})"
    result = subprocess.run(
        ["sh", "-eu", "-c", launchers[int(resume)]],
        env={
            **os.environ,
            "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}",
            "SBX_ENVIRONMENT": "/project with spaces/.sbx/custom.yaml",
            "SBX_SANDBOX_NAME": "parallel-worker-override",
            "CODEX_EXECUTABLE": str(executable),
            "SBX_GUEST_WORKDIR": str(guest),
            "CODEX_MODEL": model,
            "SBX_TASK_PROMPT": prompt,
            "SBX_TASK_LOG": str(log),
            "SBX_SESSION_ID": session_id,
            "SBX_CAPTURE": str(capture),
            "SBX_WORKER_EXIT_CODE": str(worker_exit_code),
        },
        input="Host stdin must not reach the guest.\n",
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert result.returncode == worker_exit_code, result.stderr
    evidence = json.loads(capture.read_text())
    assert evidence == {
        "argv": [
            "exec",
            *(["resume"] if resume else []),
            "--model",
            model,
            "--disable",
            "hooks",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            *([session_id] if resume else []),
            prompt,
        ],
        "sandbox_name": "parallel-worker-override",
        "workdir": str(guest),
        "stdin": "",
    }
    assert not marker.exists()
    assert set(log.read_text().splitlines()) == {"guest stderr", "guest stdout"}


@pytest.mark.parametrize("sandbox_name", [None, ""], ids=["missing", "empty"])
@pytest.mark.parametrize("resume", [False, True], ids=["launch", "resume"])
def test_codex_launcher_requires_effective_sandbox_name(sandbox_name: str | None, resume: bool) -> None:
    """Reject an absent effective name before attempting a guest launch."""
    document = (ORCHESTRATOR_DIR / "references/worker-launch.md").read_text(encoding="utf-8")
    launchers = re.findall(r"```sh\n(.*?)\n```", document, re.DOTALL)
    environment = {key: value for key, value in os.environ.items() if key != "SBX_SANDBOX_NAME"}
    environment["SBX_ENVIRONMENT"] = "/project with spaces/.sbx/custom.yaml"
    if sandbox_name is not None:
        environment["SBX_SANDBOX_NAME"] = sandbox_name
    result = subprocess.run(
        ["sh", "-eu", "-c", launchers[int(resume)]],
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "SBX_SANDBOX_NAME: Set SBX_SANDBOX_NAME to the recorded effective sandbox name" in result.stderr


def test_skill_ships_direct_mounted_project_environment_templates():
    """Keep every harness project-owned and direct-mounted by default."""
    codex = yaml.safe_load((TEMPLATES_DIR / "codex.sbxenv.yaml").read_text(encoding="utf-8"))
    agy = yaml.safe_load((TEMPLATES_DIR / "agy.sbxenv.yaml").read_text(encoding="utf-8"))
    claude = yaml.safe_load((TEMPLATES_DIR / "claude.sbxenv.yaml").read_text(encoding="utf-8"))

    assert codex["schemaVersion"] == "1"
    assert codex["agent"] == "codex"
    assert codex["workspace"] == {"path": "..", "clone": False}
    assert codex["kits"] == ["./kit"]

    assert agy["schemaVersion"] == "1"
    assert agy["agent"] == "antigravity"
    assert agy["workspace"] == {"path": "..", "clone": False}
    assert agy["kits"] == [
        "./kit",
        "git+https://github.com/docker/sbx-kits-contrib.git#ref=21e1928b5fe0036163307ea8047e48390f2d6fec&dir=antigravity",
    ]

    assert claude["schemaVersion"] == "1"
    assert claude["agent"] == "claude"
    assert claude["workspace"] == {"path": "..", "clone": False}
    assert claude["kits"] == ["./kit"]

    for environment in (codex, agy, claude):
        assert not {"secrets", "bindings", "registries", "mcp", "additionalWorkspaces"} & set(environment)


def test_skill_references_record_the_pinned_agy_supply_chain_and_boundary():
    """Keep the experimental AGY path auditable and repository-owned."""
    pin = (REFERENCES_DIR / "upstream-pins.md").read_text(encoding="utf-8")
    environment_files = (REFERENCES_DIR / "environment-files.md").read_text(encoding="utf-8")

    assert "21e1928b5fe0036163307ea8047e48390f2d6fec" in pin
    assert "6fba87a5f2e3b76003e9efe3410572cbb47d925adc8b1aaafeab2f786841b0e9" in pin
    for prohibited in ("secrets", "bindings", "registries", "local-command MCP"):
        assert prohibited in environment_files


def test_skill_documents_the_confirmation_gated_agy_kit_allowlist_prerequisite():
    """Keep the Git-pinned AGY kit usable without silently broadening host policy."""
    agents = (REFERENCES_DIR / "agents.md").read_text(encoding="utf-8")

    for required in ("kit.allowedSources", "github.com/docker/", "confirmation", "preserv"):
        assert required in agents


@pytest.mark.parametrize("skill_dir", [SKILL_DIR, ORCHESTRATOR_DIR], ids=["sandboxes", "orchestrator"])
def test_skill_has_no_host_managed_guest_customization_paths(skill_dir: Path):
    """Keep guest contents wholly owned by the consuming repository."""
    prohibited = (
        "optional-host-overlays",
        "personal.sbxenv",
        "shareSkills",
        "skills-kit",
        "codex-kit",
        ".local/share/sbx/personal",
        "tool-cache",
        "sbx.personal",
    )

    for path in skill_dir.rglob("*"):
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            for phrase in prohibited:
                assert phrase not in content, f"Unexpected {phrase!r} in {path}"
