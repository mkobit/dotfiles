from __future__ import annotations

import gzip
import importlib
import io
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from skill_filter.main import (
    TRANSFORMS,
    FilterError,
    Selection,
    filter_archive,
    main,
    parse_selection,
)

if sys.version_info >= (3, 11):
    import tomllib

# skill_filter itself must keep running on python 3.8 (see README.md), and CI
# exercises the whole suite there. tomllib arrived in 3.11, so the tests that
# validate emitted TOML against the real parser skip on older interpreters
# rather than breaking collection for every other test in the file.
requires_tomllib = pytest.mark.skipif(
    sys.version_info < (3, 11), reason="tomllib requires python 3.11+"
)

SCRIPT = Path(__file__).parent.parent / "skill_filter" / "main.py"
MAIN_MODULE = importlib.import_module("skill_filter.main")


def manifest_helper(name: str):
    helper = getattr(MAIN_MODULE, name, None)
    assert helper is not None, f"{name} is not implemented"
    return helper


def make_archive(
    entries: dict[str, bytes | None], prefix: str = "repo-abc123"
) -> io.BytesIO:
    """Build an in-memory tar.gz; a value of None creates a directory entry."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name, content in entries.items():
            info = tarfile.TarInfo(name=f"{prefix}/{name}")
            if content is None:
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            else:
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
    return io.BytesIO(gzip.compress(raw.getvalue()))


def read_archive(buffer: io.BytesIO) -> dict[str, bytes | None]:
    buffer.seek(0)
    with tarfile.open(fileobj=buffer, mode="r:") as archive:
        return {
            member.name: extracted.read()
            if (extracted := archive.extractfile(member)) is not None
            else None
            for member in archive.getmembers()
        }


def read_text(result: dict[str, bytes | None], name: str) -> str:
    """Return a file entry's decoded contents, asserting it is not a directory."""
    content = result[name]
    assert content is not None, f"{name} is a directory entry, not a file"
    return content.decode()


def run_filter(
    source: io.BytesIO,
    selections: list[Selection],
    strip_components: int = 1,
    transform_name: str | None = None,
) -> io.BytesIO:
    output = io.BytesIO()
    transform = TRANSFORMS[transform_name] if transform_name else None
    filter_archive(source, output, selections, strip_components, transform)
    return output


class TestSelection:
    def test_reroot_single_skill_to_output_root(self):
        source = make_archive(
            {
                "skills/brainstorming": None,
                "skills/brainstorming/SKILL.md": b"# brainstorm",
                "skills/brainstorming/scripts/run.py": b"print()",
                "skills/other/SKILL.md": b"# other",
                "README.md": b"readme",
            }
        )
        result = read_archive(
            run_filter(source, [parse_selection("skills/brainstorming:.")])
        )
        assert result == {
            "SKILL.md": b"# brainstorm",
            "scripts/run.py": b"print()",
        }

    def test_dest_defaults_to_src_basename(self):
        source = make_archive({"skills/brainstorming/SKILL.md": b"x"})
        result = read_archive(
            run_filter(source, [parse_selection("skills/brainstorming")])
        )
        assert result == {"brainstorming/SKILL.md": b"x"}

    def test_multiple_selections(self):
        source = make_archive(
            {
                "skills/a/SKILL.md": b"a",
                "skills/b/SKILL.md": b"b",
                "skills/c/SKILL.md": b"c",
            }
        )
        selections = [parse_selection("skills/a"), parse_selection("skills/b")]
        result = read_archive(run_filter(source, selections))
        assert set(result) == {"a/SKILL.md", "b/SKILL.md"}

    def test_explicit_dest(self):
        source = make_archive({"skills/a/SKILL.md": b"a"})
        result = read_archive(run_filter(source, [parse_selection("skills/a:renamed")]))
        assert result == {"renamed/SKILL.md": b"a"}

    def test_unmatched_selection_raises(self):
        source = make_archive({"skills/a/SKILL.md": b"a"})
        with pytest.raises(FilterError, match="skills/missing"):
            run_filter(source, [parse_selection("skills/missing")])

    def test_strip_components_zero(self):
        source = make_archive({"a/SKILL.md": b"a"}, prefix="skills")
        result = read_archive(
            run_filter(source, [parse_selection("skills/a:.")], strip_components=0)
        )
        assert result == {"SKILL.md": b"a"}


class TestSafety:
    def test_member_with_dotdot_raises(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo(name="repo/../../evil.txt")
            info.size = 4
            archive.addfile(info, io.BytesIO(b"evil"))
        source = io.BytesIO(gzip.compress(raw.getvalue()))
        with pytest.raises(FilterError, match="escapes"):
            run_filter(source, [parse_selection("anything")])

    def test_absolute_member_raises(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        source = io.BytesIO(gzip.compress(raw.getvalue()))
        with pytest.raises(FilterError, match="escapes"):
            run_filter(source, [parse_selection("anything")])

    def test_symlink_members_skipped(self, capsys):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            file_info = tarfile.TarInfo(name="repo/skills/a/SKILL.md")
            file_info.size = 1
            archive.addfile(file_info, io.BytesIO(b"x"))
            link_info = tarfile.TarInfo(name="repo/skills/a/link")
            link_info.type = tarfile.SYMTYPE
            link_info.linkname = "/etc/passwd"
            archive.addfile(link_info)
        source = io.BytesIO(gzip.compress(raw.getvalue()))
        result = read_archive(run_filter(source, [parse_selection("skills/a:.")]))
        assert result == {"SKILL.md": b"x"}
        assert "skipping link" in capsys.readouterr().err

    def test_owner_normalized(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo(name="repo/skills/a/SKILL.md")
            info.size = 1
            info.uid = 1000
            info.uname = "mkobit"
            archive.addfile(info, io.BytesIO(b"x"))
        source = io.BytesIO(gzip.compress(raw.getvalue()))
        output = run_filter(source, [parse_selection("skills/a:.")])
        output.seek(0)
        with tarfile.open(fileobj=output, mode="r:") as archive:
            member = archive.getmembers()[0]
            assert (member.uid, member.uname) == (0, "")


class TestDeterminism:
    def test_output_sorted_by_name(self):
        source = make_archive(
            {
                "skills/a/z.md": b"z",
                "skills/a/SKILL.md": b"s",
                "skills/a/b/inner.md": b"i",
            }
        )
        output = run_filter(source, [parse_selection("skills/a:.")])
        output.seek(0)
        with tarfile.open(fileobj=output, mode="r:") as archive:
            names = [member.name for member in archive.getmembers()]
        assert names == sorted(names)


AGENT_MD = b"""---
name: SRE (Site Reliability Engineer)
description: Expert site reliability engineer specializing in SLOs and error budgets.
color: "#e63946"
emoji: \xf0\x9f\x9b\xa1\xef\xb8\x8f
vibe: Reliability is a feature.
---

# Mission

A body line that is exactly
---
must survive unchanged.
"""

AGENT_AS_SKILL_MD = b"""---
name: engineering-sre
description: Expert site reliability engineer specializing in SLOs and error budgets.
---

# Mission

A body line that is exactly
---
must survive unchanged.
"""


AGENT_AS_OPENCODE_MD = b"""---
name: engineering-sre
description: Expert site reliability engineer specializing in SLOs and error budgets.
mode: subagent
---

# Mission

A body line that is exactly
---
must survive unchanged.
"""


class TestAgentSkillTransform:
    def test_rewrites_frontmatter_and_preserves_body(self):
        source = make_archive({"engineering/engineering-sre.md": AGENT_MD})
        result = read_archive(
            run_filter(
                source,
                [parse_selection("engineering/engineering-sre.md:SKILL.md")],
                transform_name="agent-skill",
            )
        )
        assert result == {"SKILL.md": AGENT_AS_SKILL_MD}

    def test_opencode_transform_adds_subagent_mode(self):
        source = make_archive({"engineering/engineering-sre.md": AGENT_MD})
        result = read_archive(
            run_filter(
                source,
                [parse_selection("engineering/engineering-sre.md")],
                transform_name="agent-opencode",
            )
        )
        assert result == {"engineering-sre.md": AGENT_AS_OPENCODE_MD}

    @requires_tomllib
    def test_codex_transform_emits_toml_parseable_by_the_real_parser(self):
        source = make_archive({"engineering/engineering-sre.md": AGENT_MD})
        result = read_archive(
            run_filter(
                source,
                [
                    parse_selection(
                        "engineering/engineering-sre.md:engineering-sre.toml"
                    )
                ],
                transform_name="agent-codex",
            )
        )
        parsed = tomllib.loads(read_text(result, "engineering-sre.toml"))
        assert set(parsed) == {"name", "description", "developer_instructions"}
        assert parsed["name"] == "engineering-sre"
        assert "\n" in parsed["developer_instructions"], "body newlines must survive"

    @requires_tomllib
    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                'Use """triple quotes""" inline.', id="toml-multiline-delimiter"
            ),
            pytest.param(r"A path like C:\Users\x and a regex \d+\.", id="backslashes"),
            pytest.param('Ends with a quote"', id="trailing-quote"),
            pytest.param("Tabs\tand\rcarriage returns", id="control-chars"),
            pytest.param("Unicode: emoji 🎨 and accents é", id="unicode"),
        ],
    )
    def test_codex_transform_round_trips_hostile_bodies(self, body):
        """The hand-rolled TOML writer must survive what real agent bodies contain."""
        agent = f"---\nname: X\ndescription: A test agent\n---\n{body}\n".encode()
        source = make_archive({"engineering/agent.md": agent})
        result = read_archive(
            run_filter(
                source,
                [parse_selection("engineering/agent.md:agent.toml")],
                transform_name="agent-codex",
            )
        )
        parsed = tomllib.loads(read_text(result, "agent.toml"))
        assert parsed["developer_instructions"] == body

    def test_codex_transform_output_shape_without_a_toml_parser(self):
        """Assert the emitted shape literally, so the 3.8 runtime still covers this path.

        The parser-backed tests above are the real check, but they need tomllib and
        so skip on the interpreter this transform actually runs on during apply.
        """
        agent = b'---\nname: X\ndescription: Does things\n---\nLine one\nsays "hi"\n'
        source = make_archive({"engineering/agent.md": agent})
        result = read_archive(
            run_filter(
                source,
                [parse_selection("engineering/agent.md:agent.toml")],
                transform_name="agent-codex",
            )
        )
        emitted = read_text(result, "agent.toml")
        assert emitted == (
            'name = "agent"\n'
            'description = "Does things"\n'
            'developer_instructions = "Line one\\nsays \\"hi\\""\n'
        )

    def test_codex_transform_rejects_oversized_description(self):
        agent = f"---\nname: X\ndescription: {'x' * 1025}\n---\nBody\n".encode()
        source = make_archive({"engineering/agent.md": agent})
        with pytest.raises(FilterError, match="over Codex's 1024"):
            run_filter(
                source,
                [parse_selection("engineering/agent.md:agent.toml")],
                transform_name="agent-codex",
            )

    def test_codex_transform_rejects_empty_description(self):
        agent = b"---\nname: X\ndescription:\n---\nBody\n"
        source = make_archive({"engineering/agent.md": agent})
        with pytest.raises(FilterError, match="empty description"):
            run_filter(
                source,
                [parse_selection("engineering/agent.md:agent.toml")],
                transform_name="agent-codex",
            )

    def test_missing_frontmatter_raises(self):
        source = make_archive({"engineering/agent.md": b"# Just a heading\n"})
        with pytest.raises(FilterError, match="no frontmatter"):
            run_filter(
                source,
                [parse_selection("engineering/agent.md:SKILL.md")],
                transform_name="agent-skill",
            )

    def test_unterminated_frontmatter_raises(self):
        source = make_archive({"engineering/agent.md": b"---\nname: x\n"})
        with pytest.raises(FilterError, match="unterminated"):
            run_filter(
                source,
                [parse_selection("engineering/agent.md:SKILL.md")],
                transform_name="agent-skill",
            )

    def test_missing_description_raises(self):
        source = make_archive({"engineering/agent.md": b"---\nname: x\n---\nbody\n"})
        with pytest.raises(FilterError, match="no description"):
            run_filter(
                source,
                [parse_selection("engineering/agent.md:SKILL.md")],
                transform_name="agent-skill",
            )


class TestSelectionParsing:
    @pytest.mark.parametrize(
        "raw", ["", "/abs", "../up", "a/../..", "a:..", "a:/abs", "."]
    )
    def test_invalid_selection_raises(self, raw):
        with pytest.raises(FilterError):
            parse_selection(raw)

    def test_src_normalized(self):
        assert parse_selection("skills//a/") == Selection(src="skills/a", dest="a")


class TestMain:
    def test_multiple_dot_dests_rejected(self, capsys):
        assert main(["--select", "a:.", "--select", "b:."]) == 1
        assert "single --select" in capsys.readouterr().err

    def test_end_to_end_via_stdio(self, monkeypatch, capsys):
        source = make_archive({"skills/a/SKILL.md": b"hello"})
        monkeypatch.setattr("sys.stdin", type("FakeStdin", (), {"buffer": source})())
        captured = io.BytesIO()
        monkeypatch.setattr(
            "sys.stdout", type("FakeStdout", (), {"buffer": captured})()
        )
        assert main(["--select", "skills/a:."]) == 0
        assert read_archive(captured) == {"SKILL.md": b"hello"}


class TestSubprocess:
    """Invoke main.py by file path with real pipes, mirroring the chezmoi external filter contract.

    BytesIO is seekable but pipes are not; these tests guard the stream-mode
    output requirement that in-memory tests cannot catch.
    """

    def run_script(
        self, *args: str, stdin: bytes
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_filters_archive_through_pipes(self):
        source = make_archive(
            {
                "skills/brainstorming/SKILL.md": b"# brainstorm",
                "skills/brainstorming/scripts/run.py": b"print()",
                "skills/other/SKILL.md": b"# other",
            }
        )
        result = self.run_script(
            "--select", "skills/brainstorming:.", stdin=source.getvalue()
        )
        assert result.returncode == 0, result.stderr.decode()
        assert read_archive(io.BytesIO(result.stdout)) == {
            "SKILL.md": b"# brainstorm",
            "scripts/run.py": b"print()",
        }

    def test_unmatched_selection_fails_with_diagnostic(self):
        source = make_archive({"skills/a/SKILL.md": b"a"})
        result = self.run_script(
            "--select", "skills/missing:.", stdin=source.getvalue()
        )
        assert result.returncode == 1
        assert b"skills/missing" in result.stderr

    def test_garbage_input_fails_cleanly(self):
        result = self.run_script("--select", "skills/a:.", stdin=b"not a tarball")
        assert result.returncode == 1
        assert result.stdout == b""

    def test_agent_skill_transform_through_pipes(self):
        source = make_archive({"engineering/engineering-sre.md": AGENT_MD})
        result = self.run_script(
            "--select",
            "engineering/engineering-sre.md:SKILL.md",
            "--transform",
            "agent-skill",
            stdin=source.getvalue(),
        )
        assert result.returncode == 0, result.stderr.decode()
        assert read_archive(io.BytesIO(result.stdout)) == {
            "SKILL.md": AGENT_AS_SKILL_MD
        }

    def test_unknown_transform_rejected(self):
        result = self.run_script(
            "--select", "a:.", "--transform", "nonsense", stdin=b""
        )
        assert result.returncode == 2
        assert b"invalid choice" in result.stderr

    def test_caching_mechanism(self, tmp_path, monkeypatch):
        # Override the user cache directory with a temporary directory
        monkeypatch.setenv("HOME", str(tmp_path))

        source = make_archive({"skills/a/SKILL.md": b"hello"})

        # First run: cache miss, should write cache file and return filtered content
        result1 = self.run_script(
            "--cache-key",
            "my-test-key",
            "--select",
            "skills/a:.",
            stdin=source.getvalue(),
        )
        assert result1.returncode == 0
        assert read_archive(io.BytesIO(result1.stdout)) == {"SKILL.md": b"hello"}

        # Verify the cache file was created
        cache_dir = tmp_path / ".cache" / "skill-filter"
        assert cache_dir.exists()
        cache_files = list(cache_dir.glob("my-test-key-*.tar"))
        assert len(cache_files) == 1

        # Second run: cache hit, should read from cache file and bypass stdin content
        result2 = self.run_script(
            "--cache-key",
            "my-test-key",
            "--select",
            "skills/a:.",
            stdin=b"garbage that would fail to decompress if read",
        )
        assert result2.returncode == 0
        assert read_archive(io.BytesIO(result2.stdout)) == {"SKILL.md": b"hello"}


class TestSkillRootManifest:
    @pytest.mark.parametrize(
        "content",
        [
            "\n",
            ".codex/skills/example",
            ".codex/skills/example\n\n",
            ".codex/skills/example \n",
            "/tmp/example\n",
            "../.codex/skills/example\n",
            ".codex/skills/group/example\n",
            ".config/opencode/skills/example\n",
        ],
    )
    def test_rejects_malformed_or_unsupported_entries(self, tmp_path, content):
        parse_manifest = manifest_helper("parse_skill_root_manifest")
        validate_manifest = manifest_helper("validate_skill_root_manifest")

        with pytest.raises(FilterError):
            entries = parse_manifest(content, allow_duplicates=True)
            validate_manifest(tmp_path, entries)

    def test_rejects_duplicate_entries_in_persisted_manifest(self, tmp_path):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"
        state_manifest.parent.mkdir(parents=True)
        state_manifest.write_text(
            ".codex/skills/example\n.codex/skills/example\n", encoding="utf-8"
        )

        with pytest.raises(FilterError, match="duplicate"):
            reconcile(tmp_path, state_manifest, ".codex/skills/example\n")

    def test_deduplicates_desired_roots(self, tmp_path):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"

        desired = reconcile(
            tmp_path,
            state_manifest,
            ".codex/skills/example\n.claude/skills/example\n.codex/skills/example\n",
        )

        assert desired == (
            ".claude/skills/example",
            ".codex/skills/example",
        )
        assert state_manifest.read_text(encoding="utf-8") == (
            ".claude/skills/example\n.codex/skills/example\n"
        )

    def test_deletes_only_stale_recorded_roots(self, tmp_path):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"
        state_manifest.parent.mkdir(parents=True)
        state_manifest.write_text(
            ".codex/skills/keep\n.codex/skills/stale\n", encoding="utf-8"
        )
        keep = tmp_path / ".codex/skills/keep"
        stale = tmp_path / ".codex/skills/stale"
        unmanaged = tmp_path / ".codex/skills/unmanaged"
        for root in (keep, stale, unmanaged):
            root.mkdir(parents=True)
            (root / "SKILL.md").write_text(root.name, encoding="utf-8")

        reconcile(tmp_path, state_manifest, ".codex/skills/keep\n")

        assert keep.is_dir()
        assert not stale.exists()
        assert unmanaged.is_dir()

    def test_rejects_symlink_escape_without_deleting_target(self, tmp_path):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"
        state_manifest.parent.mkdir(parents=True)
        state_manifest.write_text(".codex/skills/stale\n", encoding="utf-8")
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir()
        marker = outside / "marker"
        marker.write_text("keep", encoding="utf-8")
        link = tmp_path / ".codex/skills/stale"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside, target_is_directory=True)

        with pytest.raises(FilterError, match="escape|symlink"):
            reconcile(tmp_path, state_manifest, "")

        assert marker.read_text(encoding="utf-8") == "keep"

    def test_validates_every_stale_root_before_deleting_any(self, tmp_path):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"
        state_manifest.parent.mkdir(parents=True)
        state_manifest.write_text(
            ".codex/skills/a-directory\n.codex/skills/z-file\n", encoding="utf-8"
        )
        directory = tmp_path / ".codex/skills/a-directory"
        directory.mkdir(parents=True)
        invalid_file = tmp_path / ".codex/skills/z-file"
        invalid_file.write_text("not a directory", encoding="utf-8")

        with pytest.raises(FilterError, match="non-directory"):
            reconcile(tmp_path, state_manifest, "")

        assert directory.is_dir()

    def test_failed_atomic_replace_preserves_prior_manifest(
        self, tmp_path, monkeypatch
    ):
        reconcile = manifest_helper("reconcile_skill_roots")
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"
        state_manifest.parent.mkdir(parents=True)
        prior = ".codex/skills/prior\n"
        state_manifest.write_text(prior, encoding="utf-8")

        def fail_replace(src, dst):
            raise OSError("replace failed")

        monkeypatch.setattr(os, "replace", fail_replace)

        with pytest.raises(OSError, match="replace failed"):
            reconcile(tmp_path, state_manifest, ".codex/skills/desired\n")

        assert state_manifest.read_text(encoding="utf-8") == prior
        assert [path.name for path in state_manifest.parent.iterdir()] == [
            state_manifest.name
        ]

    def test_cleanup_cli_reads_desired_manifest_from_stdin(self, tmp_path):
        state_manifest = tmp_path / ".local/state/chezmoi/skill-roots.manifest"

        result = subprocess.run(
            [
                sys.executable,
                "-S",
                str(SCRIPT),
                "cleanup-skill-roots",
                "--dest-dir",
                str(tmp_path),
                "--state-manifest",
                str(state_manifest),
            ],
            input=b".cursor/skills/example\n",
            capture_output=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 0, result.stderr.decode()
        assert state_manifest.read_text(encoding="utf-8") == (
            ".cursor/skills/example\n"
        )
