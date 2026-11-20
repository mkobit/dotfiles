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
        "python@3.14": "3.14.11",
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
    [
        ("python", "3.14.10", "3.15.1"),
        ("python", "3.14.10", "4.0.0"),
        ("ollama", "0.40.16", "1.0.0"),
    ],
)
def test_publisher_rejects_mise_updates_outside_supported_series(tool: str, old: str, new: str) -> None:
    source = f'[mise.global_tools.{tool}]\nversion = "{old}"\n'
    with pytest.raises(ValueError, match="supported mise release series"):
        approved_catalog(source, source.replace(old, new), f"mise-{tool}")


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("case", ["fits", "expands", "raw-oversize", "mise-oversize"])
def test_publisher_does_not_send_mentions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool, case: str
) -> None:
    publish = PUBLISHER["publish"]
    publication = publish.__globals__
    name, old, new, original, updated = "bkt", "0.8.2", "0.8.3", BASE, NEW
    upstream = "https://github.com/example/bkt/releases"
    if case == "mise-oversize":
        name, old, new = "mise-bun", "1.2.3", "1.2.4"
        original = f'[mise.global_tools.bun]\nversion = "{old}"\n'
        updated = original.replace(old, new)
        upstream = "https://bun.com/blog/bun-v1.2.4"
    body = (
        "Thanks @alice, &#64;bob, &#x40;carol, and &commat;org/team.\n"
        "[@maintainer](https://unpkg.com/@scope/tool@1.2.3/README.md)\n"
        "Contact help@example.org. Keep &#640; and &#x400;.\n"
        "[Unclosed](https://example.org/@alice\n"
    )
    if case == "expands":
        body = "@alice, " * 8000
    elif case.endswith("oversize"):
        body = "```\n@alice\n" + "x" * 65536
    (tmp_path / f"{name}.toml").write_text(updated, encoding="utf-8")
    (tmp_path / f"{name}.json").write_text(
        json.dumps(
            [
                {
                    "changed": True,
                    "tool_name": name,
                    "old_version": old,
                    "new_version": new,
                    "pr_title": f"Update {name} from {old} to {new}",
                    "pr_body": body,
                }
            ]
        ),
        encoding="utf-8",
    )
    sent = []

    def command(*args: str, stdin: str | None = None) -> str:
        if args[:2] == ("git", "show"):
            return original
        if existing:
            assert args[:4] == ("gh", "api", "--method", "PATCH")
            assert stdin is not None
            sent.append(json.loads(stdin)["body"])
        else:
            assert args[:3] == ("gh", "pr", "create")
            sent.append(Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8"))
        return ""

    monkeypatch.setitem(publication, "command", command)
    monkeypatch.setitem(publication, "open_pr", lambda *_: {"number": 3, "head": {"sha": "head"}} if existing else None)
    monkeypatch.setitem(publication, "update_branch", lambda *_: (f"automation/bin-update-{name}", "head"))
    monkeypatch.setitem(publication, "remote_tip", lambda ref: "base" if ref == "refs/heads/main" else "head")
    publish(name, tmp_path, "base", "example/repo")
    if case != "fits":
        (published,) = sent
        intro, preview = published.split("\n\n", 1)
        assert f"[Read the full upstream release notes]({upstream})" in intro
        assert len(published) <= 65536
        assert "@alice" not in preview
        assert "@\u200balice" in preview
        return
    assert sent == [
        (
            "Thanks @\u200balice, @\u200bbob, @\u200bcarol, and @\u200borg/team.\n"
            "[@\u200bmaintainer](https://unpkg.com/%40scope/tool%401.2.3/README.md)\n"
            "Contact help@\u200bexample.org. Keep &#640; and &#x400;.\n"
            "[Unclosed](https://example.org/%40alice\n"
        )
    ]
