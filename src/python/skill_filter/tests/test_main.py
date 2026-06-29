import gzip
import io
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

SCRIPT = Path(__file__).parent.parent / "skill_filter" / "main.py"


def make_archive(entries: dict[str, bytes | None], prefix: str = "repo-abc123") -> io.BytesIO:
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
            member.name: extracted.read() if (extracted := archive.extractfile(member)) is not None else None
            for member in archive.getmembers()
        }


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
        result = read_archive(run_filter(source, [parse_selection("skills/brainstorming:.")]))
        assert result == {
            "SKILL.md": b"# brainstorm",
            "scripts/run.py": b"print()",
        }

    def test_dest_defaults_to_src_basename(self):
        source = make_archive({"skills/brainstorming/SKILL.md": b"x"})
        result = read_archive(run_filter(source, [parse_selection("skills/brainstorming")]))
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
        result = read_archive(run_filter(source, [parse_selection("skills/a:.")], strip_components=0))
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

    def test_missing_frontmatter_raises(self):
        source = make_archive({"engineering/agent.md": b"# Just a heading\n"})
        with pytest.raises(FilterError, match="no frontmatter"):
            run_filter(source, [parse_selection("engineering/agent.md:SKILL.md")], transform_name="agent-skill")

    def test_unterminated_frontmatter_raises(self):
        source = make_archive({"engineering/agent.md": b"---\nname: x\n"})
        with pytest.raises(FilterError, match="unterminated"):
            run_filter(source, [parse_selection("engineering/agent.md:SKILL.md")], transform_name="agent-skill")

    def test_missing_description_raises(self):
        source = make_archive({"engineering/agent.md": b"---\nname: x\n---\nbody\n"})
        with pytest.raises(FilterError, match="no description"):
            run_filter(source, [parse_selection("engineering/agent.md:SKILL.md")], transform_name="agent-skill")


class TestSelectionParsing:
    @pytest.mark.parametrize("raw", ["", "/abs", "../up", "a/../..", "a:..", "a:/abs", "."])
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
        monkeypatch.setattr("sys.stdout", type("FakeStdout", (), {"buffer": captured})())
        assert main(["--select", "skills/a:."]) == 0
        assert read_archive(captured) == {"SKILL.md": b"hello"}


class TestSubprocess:
    """Invoke main.py by file path with real pipes, mirroring the chezmoi external filter contract.

    BytesIO is seekable but pipes are not; these tests guard the stream-mode
    output requirement that in-memory tests cannot catch.
    """

    def run_script(self, *args: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
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
        result = self.run_script("--select", "skills/brainstorming:.", stdin=source.getvalue())
        assert result.returncode == 0, result.stderr.decode()
        assert read_archive(io.BytesIO(result.stdout)) == {
            "SKILL.md": b"# brainstorm",
            "scripts/run.py": b"print()",
        }

    def test_unmatched_selection_fails_with_diagnostic(self):
        source = make_archive({"skills/a/SKILL.md": b"a"})
        result = self.run_script("--select", "skills/missing:.", stdin=source.getvalue())
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
        assert read_archive(io.BytesIO(result.stdout)) == {"SKILL.md": AGENT_AS_SKILL_MD}

    def test_unknown_transform_rejected(self):
        result = self.run_script("--select", "a:.", "--transform", "nonsense", stdin=b"")
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
