import json
import runpy
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PUBLISHER = runpy.run_path(str(ROOT / ".github/scripts/publish-bin-updates.py"))
approved_catalog = PUBLISHER["approved_catalog"]
BASE = """[bin.bkt]
version = "0.8.2"
minimum_release_age = "60d"

[bin.bkt.github_releases]
repo = "example/bkt"

[bin.bkt.github_releases.platforms]
linux_amd64 = "x86_64"

[bin.bkt.github_releases.checksums]
linux_amd64 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
"""
NEW = BASE.replace("0.8.2", "0.8.3").replace("a" * 64, "b" * 64)


def test_publisher_uses_trusted_catalog_bytes() -> None:
    candidate = NEW.replace('version = "0.8.3"', 'version = "0.8.3" # Added by generator')
    assert approved_catalog(BASE, candidate, "bkt") == (NEW, "0.8.2", "0.8.3")


@pytest.mark.parametrize(
    "candidate",
    [
        NEW.replace("60d", "0d"),
        NEW.replace("example/bkt", "other/bkt"),
        NEW.replace("0.8.3", "0.8.1"),
        NEW.replace("b" * 64, "not a checksum"),
        NEW.replace(f'linux_amd64 = "{"b" * 64}"', f'other = "{"b" * 64}"'),
    ],
)
def test_publisher_rejects_disallowed_catalog_edit(candidate: str) -> None:
    with pytest.raises(ValueError):
        approved_catalog(BASE, candidate, "bkt")


def test_publisher_checks_remote_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(repo)], check=True)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Fixture")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "fixture@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Fixture")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "fixture@example.com")
    command = PUBLISHER["command"]
    catalog = Path("src/chezmoi/.chezmoidata/bin/bkt.toml")
    catalog.parent.mkdir(parents=True)
    catalog.write_text(BASE, encoding="utf-8")
    command("git", "add", ".")
    command("git", "-c", "commit.gpgsign=false", "commit", "-m", "Add catalog")
    command("git", "remote", "add", "origin", str(remote))
    command("git", "push", "origin", "main")
    base = command("git", "rev-parse", "HEAD").strip()
    directory = tmp_path / "index"
    directory.mkdir()
    ref = "refs/heads/automation/bin-update-bkt"

    def concurrent_push(*args, **kwargs):
        if "push" in args:
            command("git", "push", "origin", f"{base}:{ref}")
        return command(*args, **kwargs)

    update_branch = PUBLISHER["update_branch"]
    monkeypatch.setitem(update_branch.__globals__, "command", concurrent_push)
    with pytest.raises(subprocess.CalledProcessError):
        update_branch("bkt", catalog, NEW, base, directory)
    assert PUBLISHER["remote_tip"](ref) == base


MISE_BASE = """[mise.updates]
minimum_release_age = "21d"

[mise.global_tools.java]
version = "temurin-21.0.12+101.0.LTS"

[mise.global_tools.node]
version = "22.23.2"
"""
MISE_NEW = MISE_BASE.replace("temurin-21.0.12+101.0.LTS", "temurin-21.0.13+9.0.LTS")


def test_publisher_updates_only_selected_mise_pin() -> None:
    candidate = MISE_NEW.replace('version = "temurin-21.0.13+9.0.LTS"', 'version = "temurin-21.0.13+9.0.LTS" # Hint')
    assert approved_catalog(MISE_BASE, candidate, "mise-java") == (
        MISE_NEW,
        "temurin-21.0.12+101.0.LTS",
        "temurin-21.0.13+9.0.LTS",
    )


@pytest.mark.parametrize(
    "candidate",
    [
        MISE_NEW.replace("21.0.13", "25.0.13"),
        MISE_NEW.replace("21.0.13+9", "21.0.12+9"),
        MISE_NEW.replace("22.23.2", "22.23.5"),
        MISE_NEW.replace('"21d"', '"0d"'),
    ],
)
def test_publisher_rejects_disallowed_mise_pin_edit(candidate: str) -> None:
    with pytest.raises(ValueError):
        approved_catalog(MISE_BASE, candidate, "mise-java")


def test_mise_generator_isolates_updates_and_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = (
        MISE_BASE
        + """
[mise.global_tools.bun]
version = "1.4.4"

[mise.global_tools.ollama]
version = "0.40.16"

[mise.global_tools.python]
version = "3.14.10"
"""
    )
    versions = {
        "bun@1": "1.4.4",
        "java@temurin-21": "temurin-21.0.13+9.0.LTS",
        "node@22": "22.23.5",
        "python@3": "3.15.1",
    }

    def command(*args: str) -> str:
        if args[0] == "git":
            return source
        assert args[:4] == ("mise", "latest", "--minimum-release-age", "21d")
        if args[4] == "ollama@0":
            raise subprocess.CalledProcessError(1, args)
        return versions[args[4]] + "\n"

    generate_mise_updates = PUBLISHER["generate_mise_updates"]
    monkeypatch.setitem(generate_mise_updates.__globals__, "command", command)
    generate_mise_updates(tmp_path, "all")

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "failures.txt",
        "mise-java.json",
        "mise-java.toml",
        "mise-node.json",
        "mise-node.toml",
        "mise-python.json",
        "mise-python.toml",
    ]
    assert (tmp_path / "failures.txt").read_text() == "mise-ollama\n"
    for tool in ("mise-java", "mise-node", "mise-python"):
        candidate = (tmp_path / f"{tool}.toml").read_text()
        approved, old, new = approved_catalog(source, candidate, tool)
        assert approved == candidate
        report = json.loads((tmp_path / f"{tool}.json").read_text())[0]
        assert report["old_version"] == old
        assert report["new_version"] == new


@pytest.mark.parametrize(
    "tool, old, new",
    [("python", "3.14.10", "4.0.0"), ("ollama", "0.40.16", "1.0.0")],
)
def test_publisher_rejects_mise_major_updates(tool: str, old: str, new: str) -> None:
    source = f'[mise.global_tools.{tool}]\nversion = "{old}"\n'
    with pytest.raises(ValueError, match="supported mise release series"):
        approved_catalog(source, source.replace(old, new), f"mise-{tool}")
