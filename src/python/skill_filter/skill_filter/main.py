"""Filter a tar.gz archive down to selected subtrees.

Reads a gzipped tar archive on stdin and writes a plain tar archive on stdout.
This is the ``filter.command`` for chezmoi externals that deploy AI skills:
chezmoi downloads a pinned upstream repository archive, pipes it through this
tool to select and re-root individual skill directories, and extracts the
result to the target directory.

This module must remain self-contained and stdlib-only.
It runs via system ``python3`` at chezmoi apply time, before uv or mise are
installed, and is invoked by file path rather than as an installed package.

Example:
    python3 main.py --strip-components 1 --select skills/brainstorming:. < repo.tar.gz > skill.tar

Selections take the form ``src`` or ``src:dest`` where ``src`` is a directory
path inside the (prefix-stripped) archive and ``dest`` is where its contents
are placed in the output. ``dest`` defaults to the basename of ``src``; a
``dest`` of ``.`` places the subtree contents at the output root. Symlink and
hardlink members are skipped with a warning. Members with absolute paths or
``..`` components abort the run, since pinned-checksum archives should never
contain them.

``--transform`` applies a content rewrite to every selected file:
``agent-skill`` converts a Claude Code agent ``.md`` into SKILL.md form
(``name`` derived from the source file basename, ``description`` carried over
verbatim, body unchanged) for tools that consume agents as skills.
"""

import argparse
import copy
import gzip
import io
import posixpath
import sys
import tarfile
from collections.abc import Callable, Iterable, Sequence
from typing import BinaryIO, NamedTuple


class Selection(NamedTuple):
    src: str
    dest: str


class FilterError(Exception):
    """Raised when the archive or arguments are invalid."""


def parse_selection(raw: str) -> Selection:
    src, sep, dest = raw.partition(":")
    normalized_src = _normalize_relative(src, what=f"selection source {src!r}")
    normalized_dest = (
        dest
        if sep and dest == "."
        else _normalize_relative(
            dest if sep else posixpath.basename(normalized_src),
            what=f"selection destination {dest!r}",
        )
    )
    return Selection(src=normalized_src, dest=normalized_dest)


def _normalize_relative(path: str, what: str) -> str:
    normalized = posixpath.normpath(path)
    if not path or normalized.startswith(("/", "..")) or normalized == ".":
        raise FilterError(f"{what} must be a relative path inside the archive")
    return normalized


Transform = Callable[[str, bytes], bytes]


def _transform_agent_skill(src: str, content: bytes) -> bytes:
    lines = content.decode("utf-8").split("\n")
    if not lines or lines[0] != "---":
        raise FilterError(f"agent file {src!r} has no frontmatter")
    closing = next((index for index, line in enumerate(lines[1:], start=1) if line == "---"), None)
    if closing is None:
        raise FilterError(f"agent file {src!r} has unterminated frontmatter")
    description = next((line for line in lines[1:closing] if line.startswith("description:")), None)
    if description is None:
        raise FilterError(f"agent file {src!r} frontmatter has no description")
    name = posixpath.basename(src).removesuffix(".md")
    header = ("---", f"name: {name}", description, "---")
    return "\n".join((*header, *lines[closing + 1 :])).encode("utf-8")


TRANSFORMS: dict[str, Transform] = {"agent-skill": _transform_agent_skill}


def _stripped_name(name: str, strip_components: int) -> str | None:
    normalized = posixpath.normpath(name)
    if normalized.startswith(("/", "..")):
        raise FilterError(f"archive member {name!r} escapes the extraction root")
    parts = normalized.split("/")
    remainder = parts[strip_components:]
    return "/".join(remainder) if remainder else None


def _output_name(name: str, selection: Selection) -> str | None:
    if name != selection.src and not name.startswith(f"{selection.src}/"):
        return None
    remainder = name[len(selection.src) :].lstrip("/")
    if selection.dest == ".":
        return remainder or None
    return f"{selection.dest}/{remainder}" if remainder else selection.dest


def _renamed_member(member: tarfile.TarInfo, name: str, size: int | None = None) -> tarfile.TarInfo:
    # TarInfo.replace() requires python 3.12; copy manually to support older system pythons.
    renamed = copy.copy(member)
    renamed.name = name
    renamed.uid = 0
    renamed.gid = 0
    renamed.uname = ""
    renamed.gname = ""
    if size is not None:
        renamed.size = size
    return renamed


def filter_archive(
    src: BinaryIO,
    dst: BinaryIO,
    selections: Sequence[Selection],
    strip_components: int = 1,
    transform: Transform | None = None,
) -> None:
    """Copy selected, re-rooted subtrees from a tar.gz stream to a tar stream."""
    # stdin is not seekable, so buffer the archive to allow random access reads.
    buffered = io.BytesIO(gzip.decompress(src.read()))
    with tarfile.open(fileobj=buffered, mode="r:") as archive:
        triples = sorted(
            (
                (output_name, member, selection)
                for member in archive.getmembers()
                if (name := _stripped_name(member.name, strip_components)) is not None
                for selection in selections
                if (output_name := _output_name(name, selection)) is not None
            ),
            key=lambda triple: triple[0],
        )
        matched_sources = {selection.src for _, _, selection in triples}
        unmatched = [selection.src for selection in selections if selection.src not in matched_sources]
        if unmatched:
            raise FilterError(f"selections matched nothing in the archive: {', '.join(unmatched)}")
        # Stream mode: stdout is a pipe when invoked by chezmoi, and plain "w" mode seeks.
        with tarfile.open(fileobj=dst, mode="w|") as output:
            for output_name, member, selection in triples:
                if member.issym() or member.islnk():
                    print(f"skill-filter: skipping link member {member.name!r}", file=sys.stderr)
                elif member.isfile():
                    extracted = archive.extractfile(member)
                    assert extracted is not None
                    if transform is None:
                        output.addfile(_renamed_member(member, output_name), extracted)
                    else:
                        content = transform(selection.src, extracted.read())
                        output.addfile(_renamed_member(member, output_name, size=len(content)), io.BytesIO(content))
                elif member.isdir():
                    output.addfile(_renamed_member(member, output_name))
                else:
                    print(f"skill-filter: skipping special member {member.name!r}", file=sys.stderr)


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--select",
        action="append",
        required=True,
        metavar="SRC[:DEST]",
        help="subtree to keep; DEST defaults to basename of SRC, '.' re-roots contents at output root",
    )
    parser.add_argument(
        "--strip-components",
        type=int,
        default=1,
        help="leading path components to strip before matching (default 1, the GitHub archive top directory)",
    )
    parser.add_argument(
        "--transform",
        choices=sorted(TRANSFORMS),
        help="content rewrite applied to every selected file",
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        selections = [parse_selection(raw) for raw in args.select]
        if len(selections) > 1 and any(selection.dest == "." for selection in selections):
            raise FilterError("a '.' destination is only allowed with a single --select")
        transform = TRANSFORMS[args.transform] if args.transform else None
        filter_archive(sys.stdin.buffer, sys.stdout.buffer, selections, args.strip_components, transform)
    except (FilterError, tarfile.TarError, gzip.BadGzipFile, EOFError) as error:
        print(f"skill-filter: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
