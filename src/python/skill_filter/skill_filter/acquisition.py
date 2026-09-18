"""Safe helpers for isolated chezmoi external acquisition."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import stat
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path


class AcquisitionError(RuntimeError):
    """Raised when an acquisition plan or acquired tree is unsafe."""


_HEX = frozenset("0123456789abcdefABCDEF")
_PUBLICATION_TOKEN = re.compile(r"[0-9a-f]{32}\Z")
_PUBLICATION_JOURNAL = "version=1\n"


def _relative(value: object, description: str) -> str:
    if not isinstance(value, str) or not value:
        raise AcquisitionError(f"{description} must be a normalized relative path")
    if value == ".":
        return value
    components = value.split("/")
    if (
        value.startswith("/")
        or any(component in {"", ".", ".."} for component in components)
        or os.path.normpath(value) != value
    ):
        raise AcquisitionError(f"{description} must be a normalized relative path")
    return value


def _sha256(value: object, description: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in _HEX for char in value)
    ):
        raise AcquisitionError(f"{description} must be a SHA-256 digest")
    return value.lower()


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AcquisitionError(f"{description} must be a table")
    return value


def _source_id(url: str, checksum: str) -> str:
    digest = hashlib.sha256(f"{url}\0{checksum}".encode()).hexdigest()[:16]
    return f"source-{digest}"


def _source_metadata(definition: Mapping[str, object], name: str) -> dict[str, object]:
    ref = definition.get("ref", "")
    if not isinstance(ref, str):
        raise AcquisitionError(f"external source {name!r}.ref must be a string")
    archive_format = definition.get("archive_format", definition.get("format", "tar"))
    if not isinstance(archive_format, str) or not archive_format:
        raise AcquisitionError(
            f"external source {name!r}.archive_format must be a string"
        )
    if archive_format != "tar":
        raise AcquisitionError(
            f"external source {name!r}.archive_format is unsupported"
        )
    refresh_policy = definition.get("refresh_policy", "auto")
    if refresh_policy not in {"always", "auto", "never"}:
        raise AcquisitionError(f"external source {name!r}.refresh_policy is invalid")
    expected_root = definition.get("expected_root", ".")
    _relative(expected_root, f"external source {name!r}.expected_root")
    return {
        "ref": ref,
        "archive_format": archive_format,
        "expected_root": expected_root,
        "refresh_policy": refresh_policy,
    }


def build_plan(externals: Mapping[str, object]) -> dict[str, object]:
    """Normalize external skill declarations into deduplicated sources and uses."""
    sources: dict[tuple[str, str], dict[str, object]] = {}
    uses: list[dict[str, object]] = []
    selected: set[str] = set()
    for name, raw_definition in sorted(externals.items()):
        definition = _mapping(raw_definition, f"external source {name!r}")
        url = definition.get("url")
        if not isinstance(url, str) or not url:
            raise AcquisitionError(f"external source {name!r} requires a URL")
        checksum = _sha256(definition.get("sha256"), f"external source {name!r}.sha256")
        key = (url, checksum)
        metadata = _source_metadata(definition, str(name))
        source = sources.get(key)
        if source is None:
            source = {
                "id": _source_id(url, checksum),
                "url": url,
                **metadata,
                "sha256": checksum,
            }
            sources[key] = source
        else:
            for field, value in metadata.items():
                if source[field] != value:
                    raise AcquisitionError(
                        f"conflicting {field} for deduplicated source {source['id']!r}"
                    )
        skills = _mapping(
            definition.get("skills", {}), f"external source {name!r}.skills"
        )
        skills_root = definition.get("skills_root", "skills")
        if not isinstance(skills_root, str):
            raise AcquisitionError(
                f"external source {name!r}.skills_root must be a path"
            )
        _relative(skills_root, f"external source {name!r}.skills_root")
        skill_file = definition.get("skill_file")
        if skill_file is not None:
            _relative(skill_file, f"external source {name!r}.skill_file")
        for skill, state in sorted(skills.items()):
            if state == "absent":
                continue
            if not isinstance(state, str):
                raise AcquisitionError(
                    f"external skill {name!r}.{skill} has an invalid state"
                )
            if skill in selected:
                raise AcquisitionError(f"duplicate selected skill {skill!r}")
            selected.add(skill)
            select = skill_file or (
                skill if skills_root == "." else posixpath.join(skills_root, skill)
            )
            archive_select = (
                select
                if source["expected_root"] == "."
                else posixpath.join(str(source["expected_root"]), select)
            )
            filter_select = (
                f"{select}:{skill}/SKILL.md" if skill_file else f"{select}:{skill}"
            )
            archive_filter_select = (
                f"{archive_select}:{skill}/SKILL.md"
                if skill_file
                else f"{archive_select}:{skill}"
            )
            uses.append(
                {
                    "id": f"{source['id']}-{skill}",
                    "source_id": source["id"],
                    "skill": skill,
                    "state": state,
                    "select": _relative(select, f"external skill {skill!r}.select"),
                    "filter_select": filter_select,
                    "selection": {
                        "source": _relative(
                            archive_select, f"external skill {skill!r}.selection.source"
                        ),
                        "destination": _relative(
                            skill, f"external skill {skill!r}.selection.destination"
                        ),
                    },
                    "archive_filter_select": archive_filter_select,
                }
            )
    return {
        "plan_version": 1,
        "sources": sorted(sources.values(), key=lambda item: str(item["id"])),
        "uses": sorted(uses, key=lambda item: str(item["id"])),
    }


def _regular_file(path: Path, description: str) -> None:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise AcquisitionError(f"{description} is a symlink: {path}")
    if not stat.S_ISREG(mode):
        raise AcquisitionError(f"{description} is not a regular file: {path}")


def _safe_tree(path: Path, description: str) -> None:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise AcquisitionError(f"{description} is a symlink: {path}")
    if not stat.S_ISDIR(mode):
        raise AcquisitionError(f"{description} is not a directory: {path}")
    for entry in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        entry_mode = entry.lstat().st_mode
        if stat.S_ISLNK(entry_mode):
            raise AcquisitionError(f"{description} contains a symlink: {entry}")
        if not (stat.S_ISDIR(entry_mode) or stat.S_ISREG(entry_mode)):
            raise AcquisitionError(f"{description} contains a special file: {entry}")


def validate_source_tree(source: Path, expected_root: str = ".") -> Path:
    """Validate an extracted archive and return its expected content root."""
    _safe_tree(source, "acquired source")
    root_name = _relative(expected_root, "expected root")
    root = source / root_name
    if root_name != ".":
        if not root.exists():
            raise AcquisitionError(f"expected root does not exist: {root_name}")
        _safe_tree(root, "expected root")
    if root_name != "." and root.resolve() != source.resolve() / root_name:
        raise AcquisitionError("expected root escapes acquired source")
    return root


def _copy_tree(source: Path, destination: Path) -> None:
    mode = source.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise AcquisitionError(f"selected source is a symlink: {source}")
    if stat.S_ISDIR(mode):
        destination.mkdir(parents=True, exist_ok=True)
        for entry in sorted(source.iterdir(), key=lambda item: item.name):
            _copy_tree(entry, destination / entry.name)
        destination.chmod(stat.S_IMODE(mode))
        return
    if not stat.S_ISREG(mode):
        raise AcquisitionError(f"selected source is not a regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination, follow_symlinks=False)
    destination.chmod(stat.S_IMODE(mode))


def copy_selected(source_root: Path, select: str, destination: Path) -> None:
    """Copy one selected archive subtree while retaining bytes and modes."""
    relative = _relative(select, "selection")
    selected = source_root / relative
    if selected.resolve() != source_root.resolve() / relative:
        raise AcquisitionError("selection escapes acquired source")
    if not selected.exists():
        raise AcquisitionError(f"selection does not exist: {select}")
    if selected.is_dir():
        _copy_tree(selected, destination)
    else:
        _copy_tree(selected, destination / selected.name)


def ensure_cached_source(
    source: Mapping[str, object],
    cache: Path,
    *,
    offline: bool,
    fetch: Callable[[str, Path], None] | None = None,
) -> Path:
    """Return a verified cached archive, optionally fetching it when online."""
    source_id = source.get("id", "source")
    checksum = _sha256(source.get("sha256"), f"source {source_id!r}.sha256")
    url = source.get("url")
    if not isinstance(url, str) or not url:
        raise AcquisitionError(f"source {source_id!r} requires a URL")
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / checksum
    if target.exists():
        _regular_file(target, f"cached source {source_id!r}")
        if _sha256_file(target) != checksum:
            raise AcquisitionError(f"cached source {source_id!r} checksum mismatch")
        return target
    if offline:
        raise AcquisitionError(f"offline cache miss for source {source_id!r}")
    temporary = Path(tempfile.mkstemp(prefix=f".{checksum}.", dir=cache)[1])
    try:
        (fetch or _fetch)(url, temporary)
        _regular_file(temporary, f"fetched source {source_id!r}")
        if _sha256_file(temporary) != checksum:
            raise AcquisitionError(f"fetched source {source_id!r} checksum mismatch")
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch(url: str, destination: Path) -> None:
    scheme = urllib.parse.urlparse(url).scheme
    if scheme not in {"file", "https"}:
        raise AcquisitionError(f"unsupported source URL scheme: {scheme!r}")
    if url.startswith("file://"):
        source = Path(urllib.request.url2pathname(url[len("file://") :]))
        shutil.copyfile(source, destination, follow_symlinks=False)
        return
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def synthetic_apply_command(
    chezmoi: str,
    *,
    source: Path,
    destination: Path,
    config: Path,
    cache: Path,
    state: Path,
    refresh: str,
) -> list[str]:
    if refresh not in {"always", "auto", "never"}:
        raise AcquisitionError(f"invalid external refresh policy: {refresh!r}")
    return [
        chezmoi,
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
        str(state),
        "--no-tty",
        "--force",
        f"--refresh-externals={refresh}",
        "apply",
        "--include",
        "dirs,externals",
    ]


def publish_candidate(
    published: Path,
    candidate: Path,
    validate: Callable[[], None],
) -> None:
    """Validate and atomically replace a published tree, rolling back on failure."""
    published.parent.mkdir(parents=True, exist_ok=True)
    recover_publication(published, candidate)
    validate()
    token = uuid.uuid4().hex
    _validate_publication_input(published, candidate)
    backup = published.with_name(f".{published.name}.previous.{token}")
    staged_candidate = published.with_name(f".{published.name}.candidate.{token}")
    transaction = published.with_name(f".{published.name}.transaction.{token}")
    _assert_absent_or_safe(backup, "publication backup")
    _assert_absent_or_safe(staged_candidate, "publication candidate")
    had_published = published.exists()
    transaction.write_text(_PUBLICATION_JOURNAL, encoding="utf-8")
    candidate_staged = False
    published_backed_up = False
    candidate_published = False
    try:
        candidate.replace(staged_candidate)
        candidate_staged = True
        if had_published:
            published.replace(backup)
            published_backed_up = True
        staged_candidate.replace(published)
        candidate_published = True
    except BaseException:
        if candidate_published and published_backed_up:
            shutil.rmtree(published)
        if published_backed_up and backup.exists():
            backup.replace(published)
        if candidate_staged and staged_candidate.exists():
            _remove_tree_best_effort(staged_candidate)
        _unlink_best_effort(transaction)
        raise
    _remove_tree_best_effort(backup)
    if not backup.exists():
        _unlink_best_effort(transaction)


def recover_publication(published: Path, candidate: Path | None = None) -> None:
    """Recover interrupted publication transactions before doing other work."""
    published.parent.mkdir(parents=True, exist_ok=True)
    if published.is_symlink():
        raise AcquisitionError(f"published tree must not be a symlink: {published}")
    if published.exists() and not published.is_dir():
        raise AcquisitionError(f"published tree must be a directory: {published}")
    _recover_publication_transactions(published, candidate)


def _validate_publication_input(published: Path, candidate: Path) -> None:
    if candidate.parent != published.parent:
        raise AcquisitionError(
            "publication candidate must be beside the published tree"
        )
    if candidate == published:
        raise AcquisitionError(
            "publication candidate must differ from the published tree"
        )
    for path, description in (
        (published, "published tree"),
        (candidate, "publication candidate"),
    ):
        if path.is_symlink():
            raise AcquisitionError(f"{description} must not be a symlink")
        if path.exists() and not path.is_dir():
            raise AcquisitionError(f"{description} must be a directory")


def _assert_absent_or_safe(path: Path, description: str) -> None:
    if path.is_symlink():
        raise AcquisitionError(f"{description} is a symlink: {path.name}")
    if path.exists():
        raise AcquisitionError(f"{description} already exists: {path.name}")


def _unlink_best_effort(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _remove_tree_best_effort(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    except OSError:
        return False
    return not path.exists()


def _publication_journal_paths(published: Path, transaction: Path) -> tuple[Path, Path]:
    prefix = f".{published.name}.transaction."
    if transaction.parent != published.parent or not transaction.name.startswith(
        prefix
    ):
        raise AcquisitionError(f"unexpected publication journal: {transaction.name}")
    token = transaction.name[len(prefix) :]
    if not _PUBLICATION_TOKEN.fullmatch(token):
        raise AcquisitionError(f"malformed publication journal: {transaction.name}")
    backup = published.with_name(f".{published.name}.previous.{token}")
    candidate = published.with_name(f".{published.name}.candidate.{token}")
    return backup, candidate


def _recover_publication_transactions(published: Path, candidate: Path | None) -> None:
    prefix = f".{published.name}.transaction."
    journals = sorted(published.parent.glob(f"{prefix}*"))
    records: list[tuple[Path, Path, Path]] = []
    for transaction in journals:
        if transaction.is_symlink() or not transaction.is_file():
            raise AcquisitionError(
                f"publication journal must be a regular file: {transaction.name}"
            )
        try:
            content = transaction.read_text(encoding="utf-8")
        except OSError as error:
            raise AcquisitionError(
                f"cannot read publication journal: {transaction.name}"
            ) from error
        if content != _PUBLICATION_JOURNAL:
            raise AcquisitionError(f"malformed publication journal: {transaction.name}")
        backup, orphan_candidate = _publication_journal_paths(published, transaction)
        for path, description in (
            (backup, "publication backup"),
            (orphan_candidate, "publication candidate"),
        ):
            if path.is_symlink():
                raise AcquisitionError(f"{description} is a symlink: {path.name}")
            if path.exists() and not path.is_dir():
                raise AcquisitionError(f"{description} is not a directory: {path.name}")
        records.append((transaction, backup, orphan_candidate))

    for transaction, backup, orphan_candidate in records:
        if published.exists():
            backup_removed = _remove_tree_best_effort(backup)
            if orphan_candidate != candidate:
                _remove_tree_best_effort(orphan_candidate)
        elif backup.exists():
            backup.replace(published)
            _remove_tree_best_effort(orphan_candidate)
            backup_removed = True
        else:
            _remove_tree_best_effort(orphan_candidate)
            backup_removed = True
        if backup_removed:
            _unlink_best_effort(transaction)


def build_catalog_plan(catalog: Mapping[str, object]) -> dict[str, object]:
    """Resolve host URLs and normalize the external skill catalog."""
    skills = _mapping(catalog.get("skills", {}), "skill catalog")
    hosts = _mapping(skills.get("hosts", {}), "skill catalog hosts")
    externals = _mapping(skills.get("external", {}), "skill catalog externals")
    resolved: dict[str, object] = {}
    for name, raw_definition in externals.items():
        definition = dict(_mapping(raw_definition, f"external source {name!r}"))
        url = definition.get("url")
        if not url:
            host_name = definition.get("host", "github")
            host = _mapping(hosts.get(host_name), f"skill host {host_name!r}")
            url_format = host.get("url_format")
            if not isinstance(url_format, str):
                raise AcquisitionError(f"skill host {host_name!r} requires url_format")
            repo = definition.get("repo")
            ref = definition.get("ref")
            if not isinstance(repo, str) or not isinstance(ref, str):
                raise AcquisitionError(
                    f"external source {name!r} requires repo and ref"
                )
            url = url_format.replace("{repo}", repo).replace("{ref}", ref)
            definition["url"] = url
        resolved[str(name)] = definition
    plan = build_plan(resolved)
    destination_capability = catalog.get("destination_capability")
    if destination_capability is not None:
        if not isinstance(destination_capability, str) or not destination_capability:
            raise AcquisitionError(
                "skill catalog destination_capability must be a name"
            )
        plan["destination_capability"] = destination_capability
    return plan


def render_synthetic_externals(
    plan: Mapping[str, object],
    *,
    target_root: str,
    command: str,
    script: str,
    refresh_policy: str | None = None,
) -> str:
    """Render one filtered external per deduplicated source pin."""
    root = _relative(target_root, "synthetic target root")
    if root == ".":
        raise AcquisitionError("synthetic target root must not be the source root")
    sources = plan.get("sources", ())
    uses = plan.get("uses", ())
    if not isinstance(sources, list) or not isinstance(uses, list):
        raise AcquisitionError("acquisition plan sources and uses must be lists")
    uses_by_source: dict[str, list[Mapping[str, object]]] = {}
    for raw_use in uses:
        use = _mapping(raw_use, "acquisition use")
        source_id = use.get("source_id")
        if not isinstance(source_id, str):
            raise AcquisitionError("acquisition use requires source_id")
        uses_by_source.setdefault(source_id, []).append(use)

    lines: list[str] = []
    for raw_source in sources:
        source = _mapping(raw_source, "acquisition source")
        source_id = source.get("id")
        url = source.get("url")
        checksum = source.get("sha256")
        if not isinstance(source_id, str) or not isinstance(url, str):
            raise AcquisitionError("acquisition source requires id and url")
        checksum = _sha256(checksum, f"source {source_id!r}.sha256")
        archive_format = source.get("archive_format", "tar")
        if archive_format != "tar":
            raise AcquisitionError(
                f"source {source_id!r}.archive_format is unsupported"
            )
        source_refresh = source.get("refresh_policy", "auto")
        if source_refresh not in {"always", "auto", "never"}:
            raise AcquisitionError(f"source {source_id!r}.refresh_policy is invalid")
        if refresh_policy is not None and source_refresh != refresh_policy:
            continue
        source_uses = uses_by_source.get(source_id, [])
        if not source_uses:
            continue
        target = posixpath.join(root, source_id)
        args = ["-S", script, "--cache-key", checksum]
        for raw_use in sorted(source_uses, key=lambda item: str(item.get("id"))):
            select = _relative(
                raw_use.get(
                    "archive_filter_select",
                    raw_use.get("filter_select", raw_use.get("select")),
                ),
                "acquisition use selection",
            )
            args.extend(("--select", select))
        args.extend(("--expected-root", str(source.get("expected_root", "."))))
        lines.extend(
            (
                f"[{_toml_string(target)}]",
                'type = "archive"',
                f"url = {_toml_string(url)}",
                f"checksum = {{ sha256 = {_toml_string(checksum)} }}",
                "exact = true",
                f"format = {_toml_string(archive_format)}",
                f"filter = {{ command = {_toml_string(command)}, args = {_toml_array(args)} }}",
                "",
            )
        )
    return "\n".join(lines)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def copy_plan_to_aggregate(
    plan: Mapping[str, object],
    source_roots: Mapping[str, Path],
    destination: Path,
) -> Path:
    """Copy selected, verified source trees into one compiler source root."""
    destination.mkdir(parents=True, exist_ok=True)
    uses = plan.get("uses", ())
    if not isinstance(uses, list):
        raise AcquisitionError("acquisition plan uses must be a list")
    for raw_use in sorted(uses, key=lambda item: str(item.get("id"))):
        use = _mapping(raw_use, "acquisition use")
        source_id = use.get("source_id")
        skill = _relative(use.get("skill"), "acquisition use skill")
        if not isinstance(source_id, str) or source_id not in source_roots:
            raise AcquisitionError(f"missing acquired source mapping: {source_id!r}")
        selection = _mapping(use.get("selection", {}), "acquisition use selection")
        destination_name = _relative(
            selection.get("destination", skill), "acquisition use selection destination"
        )
        selected = source_roots[source_id] / destination_name
        if not selected.exists():
            raise AcquisitionError(f"filtered skill does not exist: {skill}")
        _copy_tree(selected, destination / skill)
    validate_source_tree(destination)
    return destination


def validated_source_roots(
    plan: Mapping[str, object], acquired_root: Path
) -> dict[str, Path]:
    """Validate each synthetic external tree and return its content root."""
    sources = plan.get("sources", ())
    uses = plan.get("uses", ())
    if not isinstance(sources, list):
        raise AcquisitionError("acquisition plan sources must be a list")
    if not isinstance(uses, list):
        raise AcquisitionError("acquisition plan uses must be a list")
    used_ids = {
        use.get("source_id")
        for use in uses
        if isinstance(use, Mapping) and isinstance(use.get("source_id"), str)
    }
    result: dict[str, Path] = {}
    for raw_source in sources:
        source = _mapping(raw_source, "acquisition source")
        source_id = source.get("id")
        if not isinstance(source_id, str):
            raise AcquisitionError("acquisition source requires id")
        if source_id not in used_ids:
            continue
        result[source_id] = validate_source_tree(
            acquired_root / source_id,
            ".",
        )
    return result


def build_materializer_payload(
    payload: Mapping[str, object],
    plan: Mapping[str, object],
    source_roots: Mapping[str, Path],
    aggregate: Path,
    *,
    capability: str | None = None,
) -> dict[str, object]:
    """Add the verified aggregate external source to the compiler payload."""
    uses = plan.get("uses", ())
    if not isinstance(uses, list):
        raise AcquisitionError("acquisition plan uses must be a list")
    if not uses:
        return dict(payload)
    copy_plan_to_aggregate(plan, source_roots, aggregate)
    result = dict(payload)
    bridge = dict(_mapping(result.get("plugin_bridge", {}), "plugin_bridge"))
    capabilities = dict(
        _mapping(bridge.get("capabilities", {}), "plugin_bridge.capabilities")
    )
    destination_capability = capability or plan.get("destination_capability")
    if not isinstance(destination_capability, str) or not destination_capability:
        raise AcquisitionError("acquisition plan requires destination_capability")
    definition = dict(
        _mapping(
            capabilities.get(destination_capability),
            f"capability {destination_capability!r}",
        )
    )
    if definition.get("acquisition_destination") is not True:
        raise AcquisitionError(
            f"capability {destination_capability!r} is not the declared acquisition destination"
        )
    skills = {
        str(use["skill"]): use["state"] for use in uses if isinstance(use, Mapping)
    }
    definition["source_id"] = "acquired-external-skills"
    definition["skills"] = skills
    capabilities[destination_capability] = definition
    bridge["capabilities"] = capabilities
    result["plugin_bridge"] = bridge
    acquired_sources = dict(
        _mapping(result.get("acquired_sources", {}), "acquired_sources")
    )
    acquired_sources["acquired-external-skills"] = str(aggregate)
    result["acquired_sources"] = acquired_sources
    return result


def main(argv: list[str] | None = None) -> int:
    """Transform a rendered catalog or plan into an assembly adapter artifact."""
    parser = argparse.ArgumentParser(prog="skill-acquisition")
    parser.add_argument("operation", choices=("plan", "externals", "adapter"))
    parser.add_argument("--target-root", default=".agent-plugin-acquisition")
    parser.add_argument("--command", default="python3")
    parser.add_argument("--script", default="")
    parser.add_argument("--refresh-policy", choices=("always", "auto", "never"))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--acquired-root", type=Path)
    parser.add_argument("--aggregate", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        if args.operation == "plan":
            result = build_catalog_plan(payload)
            json.dump(result, sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
        elif args.operation == "externals":
            result = render_synthetic_externals(
                payload,
                target_root=args.target_root,
                command=args.command,
                script=args.script,
                refresh_policy=args.refresh_policy,
            )
            sys.stdout.write(result)
        else:
            if (
                args.plan is None
                or args.acquired_root is None
                or args.aggregate is None
            ):
                raise AcquisitionError(
                    "adapter requires --plan, --acquired-root, and --aggregate"
                )
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            roots = validated_source_roots(plan, args.acquired_root)
            result = build_materializer_payload(payload, plan, roots, args.aggregate)
            json.dump(result, sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
    except (
        AcquisitionError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"skill-acquisition: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
