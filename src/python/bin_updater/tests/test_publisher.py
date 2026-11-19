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
