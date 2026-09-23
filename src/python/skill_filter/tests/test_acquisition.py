from __future__ import annotations

import hashlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from skill_filter import acquisition


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_archive(tmp_path: Path) -> Path:
    archive = tmp_path / "fixture.tar.gz"
    content = b"demo\n"
    with tarfile.open(archive, "w:gz") as output:
        member = tarfile.TarInfo("repo-abc123/project/skills/demo/SKILL.md")
        member.size = len(content)
        output.addfile(member, io.BytesIO(content))
    return archive


def _synthetic_chezmoi(
    tmp_path: Path,
    archive: Path,
    checksum: str,
    destination: Path,
    cache: Path,
    refresh: str,
    *,
    home: Path | None = None,
    state: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    destination.mkdir(parents=True, exist_ok=True)
    plan = acquisition.build_plan(
        {
            "fixture": {
                "url": archive.as_uri(),
                "ref": "abc123",
                "sha256": checksum,
                "expected_root": "project",
                "skills_root": "skills",
                "skills": {"demo": "present"},
            }
        }
    )
    source = tmp_path / f"synthetic-{refresh}"
    source.joinpath(".chezmoiexternals").mkdir(parents=True)
    source.joinpath(".chezmoiexternals/skills.toml").write_text(
        acquisition.render_synthetic_externals(
            plan,
            target_root=".acquired",
            command=sys.executable,
            script=str(Path(__file__).parents[1] / "skill_filter/main.py"),
        ),
        encoding="utf-8",
    )
    config = tmp_path / f"empty-{refresh}.toml"
    config.write_text("", encoding="utf-8")
    environment = os.environ.copy()
    environment["HOME"] = str(home or tmp_path / f"home-{refresh}")
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--cache",
            str(cache),
            "--config",
            str(config),
            "--config-format",
            "toml",
            "--persistent-state",
            str(state or tmp_path / f"state-{refresh}.boltdb"),
            "--no-tty",
            "--force",
            f"--refresh-externals={refresh}",
            "apply",
            "--include",
            "dirs,externals",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def test_build_plan_deduplicates_identical_source_pins():
    raw = {
        "first": {
            "url": "file:///cache/skills.tar.gz",
            "sha256": "a" * 64,
            "skills_root": "skills",
            "skills": {"one": "present"},
        },
        "second": {
            "url": "file:///cache/skills.tar.gz",
            "sha256": "a" * 64,
            "skills_root": "skills",
            "skills": {"two": "codex"},
        },
    }

    plan = acquisition.build_plan(raw)

    assert plan["plan_version"] == 1
    assert len(plan["sources"]) == 1
    assert {use["source_id"] for use in plan["uses"]} == {plan["sources"][0]["id"]}
    assert {use["skill"] for use in plan["uses"]} == {"one", "two"}


def test_build_plan_normalizes_archive_root_and_source_contract():
    plan = acquisition.build_plan(
        {
            "source": {
                "url": "https://example.invalid/source.tar.gz",
                "ref": "abc123",
                "sha256": "a" * 64,
                "expected_root": "project",
                "skills_root": "skills",
                "skills": {"demo": "present"},
            }
        }
    )

    source = plan["sources"][0]
    assert source == {
        "id": source["id"],
        "url": "https://example.invalid/source.tar.gz",
        "ref": "abc123",
        "sha256": "a" * 64,
        "archive_format": "tar",
        "expected_root": "project",
        "refresh_policy": "auto",
    }
    assert plan["uses"][0]["selection"] == {
        "source": "project/skills/demo",
        "destination": "demo",
    }


def test_build_plan_rejects_conflicting_metadata_for_deduplicated_source():
    with pytest.raises(acquisition.AcquisitionError, match="conflicting expected_root"):
        acquisition.build_plan(
            {
                "first": {
                    "url": "https://example.invalid/source.tar.gz",
                    "ref": "abc123",
                    "sha256": "a" * 64,
                    "expected_root": "one",
                    "skills": {"one": "present"},
                },
                "second": {
                    "url": "https://example.invalid/source.tar.gz",
                    "ref": "abc123",
                    "sha256": "a" * 64,
                    "expected_root": "two",
                    "skills": {"two": "present"},
                },
            }
        )


def test_build_plan_rejects_unsafe_source_and_use_paths():
    raw = {
        "broken": {
            "url": "file:///cache/skills.tar.gz",
            "sha256": "b" * 64,
            "skills_root": "../skills",
            "skills": {"ok": "present"},
        }
    }

    with pytest.raises(acquisition.AcquisitionError, match="normalized"):
        acquisition.build_plan(raw)


def test_catalog_plan_resolves_host_and_renders_one_external_per_source():
    catalog = {
        "skills": {
            "hosts": {"github": {"url_format": "https://example/{repo}/{ref}"}},
            "external": {
                "one": {
                    "repo": "owner/repo",
                    "ref": "abc",
                    "sha256": "a" * 64,
                    "expected_root": "project",
                    "skills": {"demo": "present"},
                },
                "same": {
                    "repo": "owner/repo",
                    "ref": "abc",
                    "sha256": "a" * 64,
                    "expected_root": "project",
                    "skills": {"other": "codex"},
                },
            },
        }
    }
    plan = acquisition.build_catalog_plan(catalog)
    rendered = acquisition.render_synthetic_externals(
        plan,
        target_root=".acquired",
        command="python3",
        script="/tmp/filter.py",
    )

    assert len(plan["sources"]) == 1
    assert rendered.count('type = "archive"') == 1
    assert '"--select", "project/skills/demo:demo"' in rendered
    assert '"--select", "project/skills/other:other"' in rendered
    assert '"refresh_policy": "auto"' not in rendered


def test_render_synthetic_externals_groups_sources_by_refresh_policy():
    plan = acquisition.build_plan(
        {
            "always": {
                "url": "https://example.invalid/always.tar.gz",
                "sha256": "a" * 64,
                "refresh_policy": "always",
                "skills": {"always": "present"},
            },
            "never": {
                "url": "https://example.invalid/never.tar.gz",
                "sha256": "b" * 64,
                "refresh_policy": "never",
                "skills": {"never": "present"},
            },
        }
    )

    always = acquisition.render_synthetic_externals(
        plan,
        target_root=".acquired",
        command="python3",
        script="/tmp/filter.py",
        refresh_policy="always",
    )
    never = acquisition.render_synthetic_externals(
        plan,
        target_root=".acquired",
        command="python3",
        script="/tmp/filter.py",
        refresh_policy="never",
    )

    assert "always.tar.gz" in always
    assert "never.tar.gz" not in always
    assert "never.tar.gz" in never
    assert "always.tar.gz" not in never


def test_adapter_aggregates_verified_sources_for_materializer(tmp_path: Path):
    source = tmp_path / "source"
    (source / "demo").mkdir(parents=True)
    (source / "demo/SKILL.md").write_text("demo\n", encoding="utf-8")
    plan = {
        "destination_capability": "demo",
        "sources": [{"id": "source-a", "expected_root": "."}],
        "uses": [
            {
                "id": "use-a",
                "source_id": "source-a",
                "skill": "demo",
                "state": "present",
                "select": "skills/demo",
                "selection": {"source": "skills/demo", "destination": "demo"},
            }
        ],
    }
    payload = {
        "plugin_bridge": {"capabilities": {"demo": {"acquisition_destination": True}}},
        "acquired_sources": {},
    }

    result = acquisition.build_materializer_payload(
        payload, plan, {"source-a": source}, tmp_path / "aggregate"
    )

    assert (
        result["plugin_bridge"]["capabilities"]["demo"]["source_id"]
        == "acquired-external-skills"
    )
    assert result["plugin_bridge"]["capabilities"]["demo"]["skills"] == {
        "demo": "present"
    }
    assert (tmp_path / "aggregate/demo/SKILL.md").read_text(
        encoding="utf-8"
    ) == "demo\n"


def test_filter_adapter_acquires_rooted_archive_as_selected_skill(tmp_path: Path):
    archive = tmp_path / "source.tar.gz"
    with tarfile.open(archive, "w:gz") as output:
        content = b"demo\n"
        member = tarfile.TarInfo("repo-abc123/project/skills/demo/SKILL.md")
        member.size = len(content)
        output.addfile(member, io.BytesIO(content))

    script = Path(__file__).parents[1] / "skill_filter" / "main.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--expected-root",
            "project",
            "--select",
            "project/skills/demo:demo",
        ],
        input=archive.read_bytes(),
        stdout=subprocess.PIPE,
        check=True,
    )

    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as filtered:
        assert filtered.extractfile("demo/SKILL.md").read() == b"demo\n"


def test_real_synthetic_chezmoi_offline_hit_uses_fixture_cache(tmp_path: Path):
    archive = _fixture_archive(tmp_path)
    checksum = _sha256(archive)
    source_id = acquisition.build_plan(
        {
            "fixture": {
                "url": archive.as_uri(),
                "ref": "abc123",
                "sha256": checksum,
                "expected_root": "project",
                "skills_root": "skills",
                "skills": {"demo": "present"},
            }
        }
    )["sources"][0]["id"]
    cache = tmp_path / "cache"
    home = tmp_path / "home"
    state = tmp_path / "state.boltdb"
    seeded = tmp_path / "seeded"
    seed = _synthetic_chezmoi(
        tmp_path,
        archive,
        checksum,
        seeded,
        cache,
        "always",
        home=home,
        state=state,
    )
    assert seed.returncode == 0, seed.stderr
    assert list((home / ".cache/skill-filter").glob(f"{checksum}-*.tar"))

    destination = tmp_path / "offline-hit"
    result = _synthetic_chezmoi(
        tmp_path,
        archive,
        checksum,
        destination,
        cache,
        "never",
        home=home,
        state=state,
    )

    assert result.returncode == 0, result.stderr
    assert (
        destination / ".acquired" / str(source_id) / "demo/SKILL.md"
    ).read_text() == "demo\n"


def test_real_synthetic_chezmoi_offline_miss_does_not_mutate_publication(
    tmp_path: Path,
):
    archive = tmp_path / "missing.tar.gz"
    checksum = "a" * 64
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")

    result = _synthetic_chezmoi(
        tmp_path, archive, checksum, tmp_path / "candidate", tmp_path / "cache", "never"
    )

    assert result.returncode != 0
    assert (published / "old").read_text(encoding="utf-8") == "old\n"


def test_real_synthetic_chezmoi_checksum_failure_does_not_mutate_publication(
    tmp_path: Path,
):
    archive = _fixture_archive(tmp_path)
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")

    result = _synthetic_chezmoi(
        tmp_path,
        archive,
        "b" * 64,
        tmp_path / "candidate",
        tmp_path / "cache",
        "always",
    )

    assert result.returncode != 0
    assert (published / "old").read_text(encoding="utf-8") == "old\n"


def test_cached_source_succeeds_offline_and_preserves_mode(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    cached_content = tmp_path / "cached-source"
    cached_content.write_bytes(b"cached")
    cached = cache / _sha256(cached_content)
    cached.write_bytes(b"cached")
    cached.chmod(0o751)

    result = acquisition.ensure_cached_source(
        {
            "id": "source-c",
            "url": "https://example.invalid/source.tar.gz",
            "sha256": _sha256(cached),
        },
        cache,
        offline=True,
    )

    assert result == cached
    assert stat.S_IMODE(result.stat().st_mode) == 0o751


def test_cached_source_offline_miss_fails_without_mutation(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()

    with pytest.raises(acquisition.AcquisitionError, match="offline cache miss"):
        acquisition.ensure_cached_source(
            {
                "id": "source-d",
                "url": "https://example.invalid/source.tar.gz",
                "sha256": "d" * 64,
            },
            cache,
            offline=True,
        )
    assert list(cache.iterdir()) == []


def test_cached_source_checksum_failure_is_rejected(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / ("e" * 64)).write_bytes(b"wrong")

    with pytest.raises(acquisition.AcquisitionError, match="checksum"):
        acquisition.ensure_cached_source(
            {
                "id": "source-e",
                "url": "https://example.invalid/source.tar.gz",
                "sha256": "e" * 64,
            },
            cache,
            offline=True,
        )


def test_validate_and_filter_source_rejects_bad_root_and_symlink(tmp_path: Path):
    source = tmp_path / "source"
    (source / "fixture/skills/demo").mkdir(parents=True)
    (source / "fixture/skills/demo/SKILL.md").write_text("demo\n", encoding="utf-8")

    assert (
        acquisition.validate_source_tree(source, expected_root="fixture")
        == source / "fixture"
    )
    with pytest.raises(acquisition.AcquisitionError, match="expected root"):
        acquisition.validate_source_tree(source, expected_root="missing")

    outside = tmp_path / "outside"
    outside.write_text("outside\n", encoding="utf-8")
    (source / "fixture/skills/demo/link").symlink_to(outside)
    with pytest.raises(acquisition.AcquisitionError, match="symlink"):
        acquisition.validate_source_tree(source, expected_root="fixture")


def test_filter_uses_copy_bytes_and_modes_only_for_selected_tree(tmp_path: Path):
    source = tmp_path / "source"
    selected = source / "fixture/skills/demo"
    selected.mkdir(parents=True)
    payload = selected / "SKILL.md"
    payload.write_text("demo\n", encoding="utf-8")
    payload.chmod(0o751)
    (source / "fixture/skills/other").mkdir(parents=True)
    (source / "fixture/skills/other/SKILL.md").write_text("other\n", encoding="utf-8")
    destination = tmp_path / "destination"

    acquisition.copy_selected(source / "fixture", "skills/demo", destination / "demo")

    copied = destination / "demo/SKILL.md"
    assert copied.read_bytes() == payload.read_bytes()
    assert stat.S_IMODE(copied.stat().st_mode) == 0o751
    assert not (destination / "other").exists()


def test_synthetic_command_uses_isolated_source_destination_and_policy():
    command = acquisition.synthetic_apply_command(
        "chezmoi",
        source=Path("/tmp/synthetic-source"),
        destination=Path("/tmp/acquired"),
        config=Path("/tmp/empty.toml"),
        cache=Path("/tmp/cache"),
        state=Path("/tmp/state.boltdb"),
        refresh="never",
    )

    assert command == [
        "chezmoi",
        "--source",
        "/tmp/synthetic-source",
        "--destination",
        "/tmp/acquired",
        "--cache",
        "/tmp/cache",
        "--config",
        "/tmp/empty.toml",
        "--config-format",
        "toml",
        "--persistent-state",
        "/tmp/state.boltdb",
        "--no-tty",
        "--force",
        "--refresh-externals=never",
        "apply",
        "--include",
        "dirs,externals",
    ]


def test_publish_candidate_only_after_success(tmp_path: Path):
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "new").write_text("new\n", encoding="utf-8")

    with pytest.raises(RuntimeError):
        acquisition.publish_candidate(
            published,
            candidate,
            lambda: (_ for _ in ()).throw(RuntimeError("compiler")),
        )
    assert (published / "old").read_text(encoding="utf-8") == "old\n"
    assert not (published / "new").exists()

    successful_candidate = tmp_path / "successful-candidate"
    successful_candidate.mkdir()
    (successful_candidate / "new").write_text("new\n", encoding="utf-8")
    acquisition.publish_candidate(published, successful_candidate, lambda: None)
    assert (published / "new").read_text(encoding="utf-8") == "new\n"
    assert not (published / "old").exists()


@pytest.mark.parametrize("failure_phase", ("stage", "backup", "publish"))
def test_publish_candidate_rollback_preserves_published_tree_on_rename_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_phase: str,
):
    published = tmp_path / "published"
    published.mkdir()
    old_file = published / "old"
    old_file.write_bytes(b"old\n")
    old_file.chmod(0o751)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    new_file = candidate / "new"
    new_file.write_bytes(b"new\n")
    new_file.chmod(0o711)

    def snapshot(root: Path) -> tuple[tuple[str, int, bytes], ...]:
        return tuple(
            (
                path.relative_to(root).as_posix(),
                stat.S_IMODE(path.stat().st_mode),
                path.read_bytes(),
            )
            for path in sorted(root.rglob("*"))
            if path.is_file()
        )

    before = snapshot(published)
    original_replace = Path.replace
    failed = False

    def fail_selected_replace(source: Path, target: Path) -> Path:
        nonlocal failed
        is_stage = source == candidate and target.name.startswith(
            ".published.candidate."
        )
        is_backup = source == published and target.name.startswith(
            ".published.previous."
        )
        is_publish = (
            source.name.startswith(".published.candidate.") and target == published
        )
        selected = {
            "stage": is_stage,
            "backup": is_backup,
            "publish": is_publish,
        }[failure_phase]
        if selected and not failed:
            failed = True
            raise OSError(f"injected {failure_phase} rename failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_selected_replace)
    with pytest.raises(OSError, match=f"injected {failure_phase}"):
        acquisition.publish_candidate(published, candidate, lambda: None)

    assert failed
    assert snapshot(published) == before
    assert not list(tmp_path.glob(".published.transaction.*"))
    assert not list(tmp_path.glob(".published.previous.*"))
    assert not list(tmp_path.glob(".published.candidate.*"))


def test_publish_candidate_recovers_orphaned_transaction_before_replacing(
    tmp_path: Path,
):
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")
    candidate = tmp_path / "published.candidate.new"
    candidate.mkdir()
    (candidate / "new").write_text("new\n", encoding="utf-8")
    token = "a" * 32
    backup = tmp_path / f".published.previous.{token}"
    published.replace(backup)
    transaction = tmp_path / f".published.transaction.{token}"
    transaction.write_text("version=1\n", encoding="utf-8")

    acquisition.publish_candidate(published, candidate, lambda: None)

    assert (published / "new").read_text(encoding="utf-8") == "new\n"
    assert not backup.exists()
    assert not transaction.exists()


def test_publish_candidate_ignores_backup_cleanup_failure(tmp_path: Path, monkeypatch):
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "new").write_text("new\n", encoding="utf-8")
    original_rmtree = shutil.rmtree

    def fail_backup_cleanup(path, *args, **kwargs):
        if ".previous." in str(path):
            raise OSError("simulated cleanup failure")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(acquisition.shutil, "rmtree", fail_backup_cleanup)
    acquisition.publish_candidate(published, candidate, lambda: None)

    assert (published / "new").read_text(encoding="utf-8") == "new\n"


def test_recovery_rejects_malicious_journal_without_deleting_targets(tmp_path: Path):
    published = tmp_path / "published"
    published.mkdir()
    (published / "old").write_text("old\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep\n", encoding="utf-8")
    token = "b" * 32
    journal = tmp_path / f".published.transaction.{token}"
    journal.write_text(f"{outside}\n{outside}\n", encoding="utf-8")

    with pytest.raises(
        acquisition.AcquisitionError, match="malformed publication journal"
    ):
        acquisition.recover_publication(published)

    assert (published / "old").read_text(encoding="utf-8") == "old\n"
    assert (outside / "keep").read_text(encoding="utf-8") == "keep\n"
    assert journal.exists()


def test_recovery_rejects_symlink_journal(tmp_path: Path):
    published = tmp_path / "published"
    published.mkdir()
    target = tmp_path / "journal-target"
    target.write_text("version=1\n", encoding="utf-8")
    (tmp_path / f".published.transaction.{'c' * 32}").symlink_to(target)

    with pytest.raises(acquisition.AcquisitionError, match="regular file"):
        acquisition.recover_publication(published)
