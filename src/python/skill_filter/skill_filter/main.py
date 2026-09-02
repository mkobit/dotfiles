"""Filter a tar.gz archive down to selected subtrees.

Reads a gzipped tar archive on stdin and writes a plain tar archive on stdout.
This is the ``filter.command`` for chezmoi externals that deploy AI skills:
chezmoi downloads a pinned upstream repository archive, pipes it through this
tool to select and re-root individual skill directories, and extracts the
result to the target directory.

This module must remain self-contained and stdlib-only, and must keep working on
the system ``python3``, since uv and mise are not installed yet on a fresh
machine. It is invoked by file path rather than as an installed package, by
whichever interpreter resolve-interpreter.sh picks: a uv- or mise-managed 3.11+
when one exists, because those start faster, and the system interpreter
otherwise. Holding the 3.8 floor is what makes that choice safe, since every
interpreter it can pick then behaves identically.

Example:
    python3 main.py --strip-components 1 --select skills/brainstorming:. < repo.tar.gz > skill.tar

Selections take the form ``src`` or ``src:dest`` where ``src`` is a directory
path inside the (prefix-stripped) archive and ``dest`` is where its contents
are placed in the output. ``dest`` defaults to the basename of ``src``; a
``dest`` of ``.`` places the subtree contents at the output root. Symlink and
hardlink members are skipped with a warning. Members with absolute paths or
``..`` components abort the run, since pinned-checksum archives should never
contain them.

``--transform`` applies a content rewrite to every selected file. All
transforms derive ``name`` from the source file basename, carry the
``description`` frontmatter line over verbatim, and leave the body unchanged:
``agent-skill`` converts a Claude Code agent ``.md`` into SKILL.md form for
tools that consume agents as skills; ``agent-opencode`` emits opencode agent
frontmatter (adds ``mode: subagent``).
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import os
import posixpath
import sys
import tarfile
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, BinaryIO, Callable, NamedTuple, Optional

if TYPE_CHECKING:
    from pathlib import Path


class Selection(NamedTuple):
    src: str
    dest: str


class FilterError(Exception):
    """Raised when the archive or arguments are invalid."""


ALLOWED_SKILL_ROOTS = (
    ".claude/skills",
    ".codex/skills",
    ".cursor/skills",
    ".gemini/antigravity-cli/skills",
)


def parse_skill_root_manifest(
    content: str, *, allow_duplicates: bool = False
) -> tuple[str, ...]:
    """Parse a strict newline-delimited list of destination-relative paths."""
    if not content:
        return ()
    if not content.endswith("\n"):
        raise FilterError("skill root manifest must end with a newline")
    entries = tuple(content.split("\n")[:-1])
    for entry in entries:
        if not entry or entry != entry.strip() or "\r" in entry or "\0" in entry:
            raise FilterError(f"malformed skill root manifest entry {entry!r}")
    if not allow_duplicates and len(entries) != len(set(entries)):
        raise FilterError("persisted skill root manifest contains a duplicate entry")
    return entries


def _skill_root_parent(entry: str) -> str:
    if posixpath.isabs(entry) or posixpath.normpath(entry) != entry or "\\" in entry:
        raise FilterError(f"skill root {entry!r} must be a normalized relative path")
    for parent in ALLOWED_SKILL_ROOTS:
        prefix = f"{parent}/"
        if entry.startswith(prefix):
            skill_name = entry[len(prefix) :]
            if not skill_name or "/" in skill_name or skill_name in (".", ".."):
                raise FilterError(
                    f"skill root {entry!r} must be a direct child of {parent!r}"
                )
            return parent
    raise FilterError(f"skill root {entry!r} is not under an allowed skills directory")


def _is_within(parent: Path, child: Path) -> bool:
    try:
        return os.path.commonpath((str(parent), str(child))) == str(parent)
    except ValueError:
        return False


def validate_skill_root_manifest(
    dest_dir: Path, entries: Iterable[str]
) -> tuple[Path, ...]:
    """Resolve manifest entries without permitting traversal or symlink escapes."""
    from pathlib import Path

    destination = Path(dest_dir)
    if not destination.is_absolute():
        raise FilterError("destination directory must be absolute")
    resolved_destination = destination.resolve()
    validated = []
    for entry in entries:
        parent = _skill_root_parent(entry)
        resolved_parent = (destination / parent).resolve()
        resolved_entry = (destination / entry).resolve()
        if not _is_within(resolved_destination, resolved_parent):
            raise FilterError(f"allowed skill root {parent!r} escapes the destination")
        if resolved_entry.parent != resolved_parent:
            raise FilterError(
                f"skill root {entry!r} escapes its allowed skills directory"
            )
        validated.append(destination / entry)
    return tuple(validated)


def _replace_manifest_atomically(state_manifest: Path, content: str) -> None:
    import tempfile

    state_manifest.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=str(state_manifest.parent), prefix=f".{state_manifest.name}."
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, state_manifest)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def reconcile_skill_roots(
    dest_dir: Path, state_manifest: Path, desired_manifest: str
) -> tuple[str, ...]:
    """Delete stale managed skill roots and atomically record desired roots."""
    import shutil
    from pathlib import Path

    destination = Path(dest_dir)
    manifest = Path(state_manifest)
    desired_entries = parse_skill_root_manifest(desired_manifest, allow_duplicates=True)
    desired = tuple(sorted(set(desired_entries)))
    validate_skill_root_manifest(destination, desired)

    prior = ()
    if manifest.exists():
        prior = parse_skill_root_manifest(manifest.read_text(encoding="utf-8"))
        prior_paths = validate_skill_root_manifest(destination, prior)
        prior_by_entry = dict(zip(prior, prior_paths))
        stale_roots = tuple(
            (stale, prior_by_entry[stale])
            for stale in sorted(set(prior) - set(desired))
        )
        for stale, stale_path in stale_roots:
            if stale_path.is_symlink():
                raise FilterError(f"refusing to delete symlink skill root {stale!r}")
            if stale_path.exists() and not stale_path.is_dir():
                raise FilterError(
                    f"refusing to delete non-directory skill root {stale!r}"
                )
        for _stale, stale_path in stale_roots:
            if stale_path.exists():
                shutil.rmtree(stale_path)

    rendered = "".join(f"{entry}\n" for entry in desired)
    _replace_manifest_atomically(manifest, rendered)
    return desired


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


class _AgentParts(NamedTuple):
    name: str
    description: str
    body: tuple[str, ...]


def _parse_agent(src: str, content: bytes) -> _AgentParts:
    lines = content.decode("utf-8").split("\n")
    if not lines or lines[0] != "---":
        raise FilterError(f"agent file {src!r} has no frontmatter")
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line == "---"), None
    )
    if closing is None:
        raise FilterError(f"agent file {src!r} has unterminated frontmatter")
    description = next(
        (line for line in lines[1:closing] if line.startswith("description:")), None
    )
    if description is None:
        raise FilterError(f"agent file {src!r} frontmatter has no description")
    basename = posixpath.basename(src)
    name = basename[: -len(".md")] if basename.endswith(".md") else basename
    return _AgentParts(
        name=name, description=description, body=tuple(lines[closing + 1 :])
    )


def _transform_agent_skill(src: str, content: bytes) -> bytes:
    parts = _parse_agent(src, content)
    header = ("---", f"name: {parts.name}", parts.description, "---")
    return "\n".join((*header, *parts.body)).encode("utf-8")


def _transform_agent_opencode(src: str, content: bytes) -> bytes:
    # An explicit name overrides opencode's path-derived agent name, which
    # would otherwise contain the source subdirectory (e.g. "src/agent-name").
    parts = _parse_agent(src, content)
    header = ("---", f"name: {parts.name}", parts.description, "mode: subagent", "---")
    return "\n".join((*header, *parts.body)).encode("utf-8")


# Codex enforces these when loading an agent role and skips the file with a
# startup warning if either is exceeded. Failing here instead surfaces the
# problem at apply time rather than as a silently missing agent.
_CODEX_NAME_LIMIT = 64
_CODEX_DESCRIPTION_LIMIT = 1024

_TOML_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _toml_basic_string(value: str) -> str:
    """Quote a str as a TOML basic string.

    Single-line form with escaped newlines, deliberately, rather than the more
    readable multi-line \"\"\" form: agent bodies are arbitrary prose that
    already contains \"\"\" and trailing quotes in practice, and every one of
    those is a delimiter edge case. A basic string has exactly one escaping
    rule, so this stays correct without special cases.
    """
    out = []
    for char in value:
        if char in _TOML_ESCAPES:
            out.append(_TOML_ESCAPES[char])
        elif char < " " or char == "\x7f":
            out.append(f"\\u{ord(char):04X}")
        else:
            out.append(char)
    return '"{}"'.format("".join(out))


def _transform_agent_codex(src: str, content: bytes) -> bytes:
    """Rewrite a Claude Code agent .md into a Codex agent role .toml.

    Codex discovers <config>/agents/**/*.toml and requires name, description,
    and developer_instructions; the markdown body becomes the instructions.
    """
    parts = _parse_agent(src, content)
    _, _, description = parts.description.partition(":")
    description = description.strip()
    if not description:
        raise FilterError(f"agent file {src!r} has an empty description")
    if len(parts.name) > _CODEX_NAME_LIMIT:
        raise FilterError(
            f"agent file {src!r} name is {len(parts.name)} chars, over Codex's {_CODEX_NAME_LIMIT}"
        )
    if len(description) > _CODEX_DESCRIPTION_LIMIT:
        raise FilterError(
            f"agent file {src!r} description is {len(description)} chars, over Codex's {_CODEX_DESCRIPTION_LIMIT}"
        )
    body = "\n".join(parts.body).strip()
    fields = (
        f"name = {_toml_basic_string(parts.name)}",
        f"description = {_toml_basic_string(description)}",
        f"developer_instructions = {_toml_basic_string(body)}",
    )
    return "{}\n".format("\n".join(fields)).encode("utf-8")


TRANSFORMS: dict[str, Transform] = {
    "agent-skill": _transform_agent_skill,
    "agent-opencode": _transform_agent_opencode,
    "agent-codex": _transform_agent_codex,
}


def _stripped_name(name: str, strip_components: int) -> Optional[str]:
    normalized = posixpath.normpath(name)
    if normalized.startswith(("/", "..")):
        raise FilterError(f"archive member {name!r} escapes the extraction root")
    parts = normalized.split("/")
    remainder = parts[strip_components:]
    return "/".join(remainder) if remainder else None


def _output_name(name: str, selection: Selection) -> Optional[str]:
    if name != selection.src and not name.startswith(f"{selection.src}/"):
        return None
    remainder = name[len(selection.src) :].lstrip("/")
    if selection.dest == ".":
        return remainder or None
    return f"{selection.dest}/{remainder}" if remainder else selection.dest


def _renamed_member(
    member: tarfile.TarInfo, name: str, size: Optional[int] = None
) -> tarfile.TarInfo:
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
    transform: Optional[Transform] = None,
) -> None:
    """Copy selected, re-rooted subtrees from a tar.gz stream to a tar stream."""
    matched_triples = []
    matched_sources = set()

    with tarfile.open(fileobj=src, mode="r|gz") as archive:
        for member in archive:
            name = _stripped_name(member.name, strip_components)
            if name is None:
                continue
            for selection in selections:
                output_name = _output_name(name, selection)
                if output_name is not None:
                    matched_sources.add(selection.src)
                    content = None
                    if member.isfile():
                        extracted = archive.extractfile(member)
                        if extracted is not None:
                            if transform is None:
                                content = extracted.read()
                            else:
                                content = transform(selection.src, extracted.read())
                    matched_triples.append((output_name, member, selection, content))
                    break

    unmatched = [
        selection.src
        for selection in selections
        if selection.src not in matched_sources
    ]
    if unmatched:
        raise FilterError(
            f"selections matched nothing in the archive: {', '.join(unmatched)}"
        )

    # Sort output by name to satisfy TestDeterminism
    matched_triples.sort(key=lambda x: x[0])

    with tarfile.open(fileobj=dst, mode="w|") as output:
        for output_name, member, _selection, content in matched_triples:
            if member.issym() or member.islnk():
                print(
                    f"skill-filter: skipping link member {member.name!r}",
                    file=sys.stderr,
                )
            elif member.isfile():
                if content is not None:
                    output.addfile(
                        _renamed_member(member, output_name, size=len(content)),
                        io.BytesIO(content),
                    )
            elif member.isdir():
                output.addfile(_renamed_member(member, output_name))
            else:
                print(
                    f"skill-filter: skipping special member {member.name!r}",
                    file=sys.stderr,
                )


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
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
    parser.add_argument(
        "--cache-key",
        help="cache key (usually the source archive SHA256) to enable caching of filtered output",
    )
    return parser.parse_args(list(argv))


def _parse_cleanup_args(argv: Iterable[str]) -> argparse.Namespace:
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog="skill-filter cleanup-skill-roots",
        description="prune stale managed AI skill directories from a destination",
    )
    parser.add_argument(
        "--dest-dir",
        required=True,
        type=Path,
        help="chezmoi destination directory",
    )
    parser.add_argument(
        "--state-manifest",
        required=True,
        type=Path,
        help="persisted manifest of roots managed by the previous run",
    )
    return parser.parse_args(list(argv))


def main(argv: Optional[Sequence[str]] = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv[:1] == ["cleanup-skill-roots"]:
        args = _parse_cleanup_args(raw_argv[1:])
        try:
            reconcile_skill_roots(
                args.dest_dir,
                args.state_manifest,
                sys.stdin.read(),
            )
        except (FilterError, OSError, UnicodeError) as error:
            print(f"skill-filter: {error}", file=sys.stderr)
            return 1
        return 0

    args = _parse_args(raw_argv)
    try:
        selections = [parse_selection(raw) for raw in args.select]
        if len(selections) > 1 and any(
            selection.dest == "." for selection in selections
        ):
            raise FilterError(
                "a '.' destination is only allowed with a single --select"
            )
        transform = TRANSFORMS[args.transform] if args.transform else None

        cache_file = None
        if args.cache_key:
            # Generate a stable hash of the selections and transforms
            args_str = f"select={sorted(args.select)},transform={args.transform},strip={args.strip_components}"
            args_hash = hashlib.sha256(args_str.encode("utf-8")).hexdigest()
            cache_dir = os.path.expanduser("~/.cache/skill-filter")
            cache_file = os.path.join(cache_dir, f"{args.cache_key}-{args_hash}.tar")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "rb") as f:
                        cache_data = f.read()
                    sys.stdout.buffer.write(cache_data)
                    # Discard stdin to avoid SIGPIPE in parent
                    while sys.stdin.buffer.read(1024 * 1024):
                        pass
                    return 0
                except Exception as e:  # noqa: BLE001  # cache read is best-effort; any failure falls back to a full rebuild
                    print(f"skill-filter cache read error: {e}", file=sys.stderr)

        if cache_file:
            output_buffer = io.BytesIO()
            filter_archive(
                sys.stdin.buffer,
                output_buffer,
                selections,
                args.strip_components,
                transform,
            )
            output_data = output_buffer.getvalue()
            sys.stdout.buffer.write(output_data)
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, "wb") as f:
                    f.write(output_data)
            except Exception as e:  # noqa: BLE001  # cache write is best-effort; any failure just skips caching
                print(f"skill-filter cache write error: {e}", file=sys.stderr)
        else:
            filter_archive(
                sys.stdin.buffer,
                sys.stdout.buffer,
                selections,
                args.strip_components,
                transform,
            )

    except (FilterError, tarfile.TarError, gzip.BadGzipFile, EOFError) as error:
        print(f"skill-filter: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
