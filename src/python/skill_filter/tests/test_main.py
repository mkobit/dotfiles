import gzip
import io
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from skill_filter.main import FilterError, Selection, filter_archive, main, parse_selection

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


def run_filter(source: io.BytesIO, selections: list[Selection], strip_components: int = 1) -> io.BytesIO:
    output = io.BytesIO()
    filter_archive(source, output, selections, strip_components)
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
