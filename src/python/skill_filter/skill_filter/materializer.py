"""Compile normalized agent-plugin declarations into deterministic source state."""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path


class MaterializerError(RuntimeError):
    """Raised when declarations or source assets are unsafe or incomplete."""


_PLAN_VERSION = 1
_PUBLICATION_TOKEN = re.compile(r"[0-9a-f]{32}\Z")
_PUBLICATION_JOURNAL = "version=1\n"
_HOSTS = ("claude", "codex", "cursor")
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_SOURCE_ATTRIBUTE_PREFIXES = (
    "remove_",
    "external_",
    "exact_",
    "private_",
    "readonly_",
    "dot_",
    "empty_",
    "encrypted_",
    "executable_",
    "once_",
    "onchange_",
    "template_",
    "create_",
    "modify_",
    "run_",
    "symlink_",
    "literal_",
)


def _validate_plan_version(payload: Mapping[str, object]) -> None:
    version = payload.get("plan_version")
    if type(version) is not int or version != _PLAN_VERSION:
        raise MaterializerError(f"unsupported plan version: {version!r}")


@contextmanager
def _materialization_lock(output: Path) -> Iterator[None]:
    """Serialize recovery and publication for one output source root."""
    descriptor = os.open(output, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _is_relative_to(path: Path, root: Path) -> bool:
    """Return whether path is lexically contained by root on Python 3.8+."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _table(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MaterializerError(f"{description} must be a table")
    return value


def _name(value: object, description: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or any(character not in _NAME_CHARS for character in value)
    ):
        raise MaterializerError(f"invalid {description} name: {value!r}")
    return value


def _path(value: object, description: str, *, absolute: bool) -> Path:
    if not isinstance(value, str) or not value:
        raise MaterializerError(f"{description} must be a non-empty path")
    path = Path(value)
    if absolute != path.is_absolute():
        kind = "absolute" if absolute else "relative"
        raise MaterializerError(f"{description} must be a normalized {kind} path")
    components = value.split("/")[1:] if absolute else value.split("/")
    if (
        any(component in {"", ".", ".."} for component in components)
        or os.path.normpath(value) != value
    ):
        kind = "absolute" if absolute else "relative"
        raise MaterializerError(f"{description} must be a normalized {kind} path")
    return path


def _source(root: Path, relative: object, description: str) -> Path:
    path = root / _path(relative, description, absolute=False)
    if path.resolve() != root.resolve() / path.relative_to(root):
        raise MaterializerError(f"{description} contains a symlink or escapes its root")
    return path


def _source_root(path: Path, description: str) -> None:
    mode = path.lstat().st_mode if os.path.lexists(path) else 0
    if not mode:
        raise MaterializerError(f"{description} does not exist: {path}")
    if stat.S_ISLNK(mode):
        raise MaterializerError(f"{description} is a symlink: {path}")
    if not stat.S_ISDIR(mode):
        raise MaterializerError(f"{description} is not a directory: {path}")


def _copy_tree(
    source: Path,
    destination: Path,
    description: str = "declared source",
    source_attribute_dirs: set[Path] | None = None,
    encode_source_files: bool = False,
) -> None:
    _source_root(source, description)
    destination.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = entry.relative_to(source)
        mode = entry.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise MaterializerError(f"{description} contains a symlink: {entry}")
        target_name = (
            _encode_source_file_name(entry.name) if encode_source_files else entry.name
        )
        target = destination / relative.with_name(target_name)
        if stat.S_ISDIR(mode):
            target.mkdir(parents=True, exist_ok=True)
            if source_attribute_dirs is not None and entry.name.startswith(
                _SOURCE_ATTRIBUTE_PREFIXES
            ):
                source_attribute_dirs.add(target)
        elif stat.S_ISREG(mode):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(entry, target, follow_symlinks=False)
            target.chmod(stat.S_IMODE(mode))
        else:
            raise MaterializerError(f"{description} contains a special file: {entry}")


def _validate_tree(source: Path, description: str) -> None:
    _source_root(source, description)
    for entry in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        mode = entry.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise MaterializerError(f"{description} contains a symlink: {entry}")
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise MaterializerError(f"{description} contains a special file: {entry}")


def _hosts(
    definition: Mapping[str, object], marketplace: Mapping[str, object]
) -> tuple[str, ...]:
    raw = definition.get("hosts", marketplace.get("hosts", ()))
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise MaterializerError("plugin hosts must be a list")
    if any(not isinstance(host, str) for host in raw):
        raise MaterializerError(f"plugin hosts must contain strings: {raw!r}")
    hosts = tuple(raw)
    if any(host not in _HOSTS for host in hosts):
        raise MaterializerError(f"unsupported plugin host in {hosts!r}")
    return tuple(sorted(set(hosts)))


def _marketplace(
    marketplaces: Mapping[str, object], name: object, description: str
) -> Mapping[str, object]:
    marketplace_name = _name(name, "marketplace")
    if marketplace_name not in marketplaces:
        raise MaterializerError(
            f"undeclared marketplace {marketplace_name!r} for {description}"
        )
    return _table(marketplaces[marketplace_name], f"marketplace {marketplace_name!r}")


def _skill_destinations(
    state: object,
    hosts: Sequence[str],
    *,
    environment: str,
    local_allowed: bool = False,
) -> tuple[str, ...]:
    if state == "present":
        return ("skills", *(f"{host}/skills" for host in hosts))
    if state == "absent" or (
        state == "local" and local_allowed and environment != "local"
    ):
        return ()
    if state == "local" and local_allowed:
        return ("skills", *(f"{host}/skills" for host in hosts))
    if state in _HOSTS and state not in hosts:
        raise MaterializerError(
            f"skill state {state!r} selects a host not declared by the capability"
        )
    if isinstance(state, str) and state in hosts:
        return (f"{state}/skills",)
    raise MaterializerError(f"invalid skill state: {state!r}")


def _enabled(definition: Mapping[str, object], environment: str) -> bool:
    raw = definition.get("environments")
    if raw is None:
        return True
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise MaterializerError("capability environments must be a list")
    if any(not isinstance(item, str) for item in raw):
        raise MaterializerError("capability environments must contain strings")
    return environment in raw


def _add_skill(
    package: Path,
    source: Path,
    skill_name: object,
    state: object,
    hosts: Sequence[str],
    environment: str,
    *,
    local_allowed: bool = False,
) -> None:
    name = _name(skill_name, "skill")
    for destination in _skill_destinations(
        state, hosts, environment=environment, local_allowed=local_allowed
    ):
        _copy_tree(
            source / name,
            package / destination / name,
            "declared skill source",
            encode_source_files=True,
        )


def _relative_source(source: Path, definition: Mapping[str, object], key: str) -> Path:
    raw = definition.get(key)
    if raw is None:
        return source
    if not isinstance(raw, str) or raw == "":
        raise MaterializerError(f"{key} must be a normalized relative path")
    if raw == ".":
        return source
    relative = _path(raw, key, absolute=False)
    path = source / relative
    if path.resolve() != source.resolve() / relative:
        raise MaterializerError(f"{key} contains a symlink or escapes its root")
    return path


def _acquired_source(
    definition: Mapping[str, object],
    acquired_sources: Mapping[str, object],
    working_tree: Path,
) -> Path | None:
    source_id = definition.get("source_id")
    if source_id is None:
        return None
    source_name = _name(source_id, "source")
    if source_name not in acquired_sources:
        raise MaterializerError(f"missing acquired source mapping: {source_name!r}")
    value = acquired_sources[source_name]
    root = _path(value, f"acquired source {source_name!r}", absolute=True)
    if root == working_tree or _is_relative_to(root, working_tree):
        raise MaterializerError(
            f"acquired source {source_name!r} must be an acquired directory"
        )
    _source_root(root, f"acquired source {source_name!r}")
    return _relative_source(root, definition, "source_root")


def _validate_skill_sources(
    source: Path,
    declared: Mapping[str, object],
    hosts: Sequence[str],
    environment: str,
    description: str,
    *,
    local_allowed: bool = False,
) -> None:
    for raw_name, state in sorted(declared.items()):
        name = _name(raw_name, "skill")
        destinations = _skill_destinations(
            state,
            hosts,
            environment=environment,
            local_allowed=local_allowed,
        )
        if destinations:
            _validate_tree(source / name, f"{description} skill source")


def _validate_skill_ownership(
    definition: Mapping[str, object],
    skills: Mapping[str, object],
    overlay_skills: Mapping[str, object],
    hosts: Sequence[str],
    environment: str,
) -> None:
    owners: dict[str, str] = {}
    sources: list[tuple[str, Mapping[str, object], bool]] = []
    if definition.get("source_id") is not None:
        sources.append(
            ("acquired", _table(definition.get("skills", {}), "skills"), False)
        )
    if definition.get("source_dir") is not None:
        sources.append(
            ("capability", _table(definition.get("skills", {}), "skills"), False)
        )
    if definition.get("authored_skill_source") is not None:
        sources.append(
            ("authored", _table(skills.get("authored", {}), "skills.authored"), False)
        )
    if definition.get("overlay_skill_source") is not None:
        sources.append(
            (
                "overlay",
                _table(overlay_skills.get("authored", {}), "overlay_skills.authored"),
                True,
            )
        )
    for source_name, declared, local_allowed in sources:
        for raw_skill, state in declared.items():
            name = _name(raw_skill, "skill")
            for destination in _skill_destinations(
                state,
                hosts,
                environment=environment,
                local_allowed=local_allowed,
            ):
                target = f"{destination}/{name}"
                previous = owners.get(target)
                if previous is not None:
                    raise MaterializerError(
                        f"duplicate skill destination {target!r}: {previous} and {source_name}"
                    )
                owners[target] = source_name


def _validate_capability(
    name: str,
    definition: Mapping[str, object],
    marketplaces: Mapping[str, object],
    skills: Mapping[str, object],
    overlay_skills: Mapping[str, object],
    acquired_sources: Mapping[str, object],
    working_tree: Path,
    environment: str,
) -> None:
    marketplace = _marketplace(
        marketplaces, definition.get("marketplace"), f"capability {name!r}"
    )
    hosts = _hosts(definition, marketplace)
    _enabled(definition, environment)

    wrapper_source = _source(
        working_tree,
        definition.get("wrapper_source_dir"),
        f"wrapper source for capability {name!r}",
    )
    _validate_tree(wrapper_source, "wrapper source")
    if "cursor" in hosts:
        _validate_tree(wrapper_source / "cursor", "cursor wrapper source")

    declared = _table(definition.get("skills", {}), f"capability {name!r} skills")
    source_id = definition.get("source_id")
    if source_id is not None:
        acquired = _acquired_source(definition, acquired_sources, working_tree)
        assert acquired is not None
        _validate_tree(acquired, "acquired skill source")
        _validate_skill_sources(
            acquired,
            declared,
            hosts,
            environment,
            "acquired",
        )

    authored_source = definition.get("authored_skill_source")
    if authored_source is not None:
        authored_root = _source(working_tree, authored_source, "authored skill source")
        _validate_tree(authored_root, "authored skill source")
        authored = _table(skills.get("authored", {}), "skills.authored")
        _validate_skill_sources(
            authored_root,
            authored,
            hosts,
            environment,
            "authored",
        )

    plugin_source = definition.get("source_dir")
    if plugin_source is not None:
        root = _source(working_tree, plugin_source, "capability source")
        _validate_tree(root, "capability source")
        skills_root = root / "skills"
        _validate_tree(skills_root, "capability skill source")
        _validate_skill_sources(
            skills_root,
            declared,
            hosts,
            environment,
            "capability",
        )

    overlay_source = definition.get("overlay_skill_source")
    if overlay_source is not None:
        root = _source(working_tree, overlay_source, "overlay skill source")
        _validate_tree(root, "overlay skill source")
        authored = _table(overlay_skills.get("authored", {}), "overlay_skills.authored")
        _validate_skill_sources(
            root,
            authored,
            hosts,
            environment,
            "overlay",
            local_allowed=True,
        )

    _validate_skill_ownership(definition, skills, overlay_skills, hosts, environment)


def _validate_plugin(
    name: str,
    definition: Mapping[str, object],
    marketplaces: Mapping[str, object],
    acquired_sources: Mapping[str, object],
    working_tree: Path,
    environment: str,
) -> None:
    marketplace = _marketplace(
        marketplaces, definition.get("marketplace"), f"plugin {name!r}"
    )
    hosts = _hosts(definition, marketplace)
    _enabled(definition, environment)

    cursor_source_id = definition.get("cursor_source_id")
    cursor_source_dir = definition.get("cursor_source_dir")
    if cursor_source_id is not None:
        cursor_source = _acquired_source(
            {
                "source_id": cursor_source_id,
                "source_root": definition.get("cursor_source_root", "."),
            },
            acquired_sources,
            working_tree,
        )
        assert cursor_source is not None
        _validate_tree(cursor_source, "cursor plugin source")
    elif cursor_source_dir is not None:
        cursor_source = _source(
            working_tree,
            cursor_source_dir,
            f"cursor plugin source for {name!r}",
        )
        _validate_tree(cursor_source, "cursor plugin source")
    elif "cursor" in hosts:
        raise MaterializerError(f"cursor plugin source for {name!r} is required")


def _build_package(
    name: str,
    definition: Mapping[str, object],
    marketplaces: Mapping[str, object],
    skills: Mapping[str, object],
    overlay_skills: Mapping[str, object],
    acquired_sources: Mapping[str, object],
    working_tree: Path,
    stage: Path,
    environment: str,
) -> tuple[Path, bool, set[Path]]:
    marketplace = _marketplace(
        marketplaces, definition.get("marketplace"), f"capability {name!r}"
    )
    hosts = _hosts(definition, marketplace)
    wrapper_source = _source(
        working_tree,
        definition.get("wrapper_source_dir"),
        f"wrapper source for capability {name!r}",
    )
    # The capability directory is an exact source boundary as well as the
    # collection root.  Without the nested ``exact_`` marker, chezmoi tracks
    # only files present in the source and leaves removed descendants behind
    # in the deployed capability directory.
    package = stage / f"exact_{name}"
    source_attribute_dirs: set[Path] = set()
    _copy_tree(wrapper_source, package, "wrapper source", source_attribute_dirs)

    acquired = _acquired_source(definition, acquired_sources, working_tree)
    if acquired is not None:
        declared = _table(definition.get("skills", {}), f"capability {name!r} skills")
        for skill_name, state in sorted(declared.items()):
            _add_skill(
                package,
                acquired,
                skill_name,
                state,
                hosts,
                environment,
            )

    authored_source = definition.get("authored_skill_source")
    if authored_source is not None:
        authored_root = _source(working_tree, authored_source, "authored skill source")
        authored = _table(skills.get("authored", {}), "skills.authored")
        for skill_name, state in sorted(authored.items()):
            _add_skill(
                package,
                authored_root,
                skill_name,
                state,
                hosts,
                environment,
            )

    plugin_source = definition.get("source_dir")
    if plugin_source is not None:
        root = _source(working_tree, plugin_source, "capability source") / "skills"
        declared = _table(definition.get("skills", {}), f"capability {name!r} skills")
        for skill_name, state in sorted(declared.items()):
            _add_skill(
                package,
                root,
                skill_name,
                state,
                hosts,
                environment,
            )

    overlay_source = definition.get("overlay_skill_source")
    if overlay_source is not None:
        root = _source(working_tree, overlay_source, "overlay skill source")
        authored = _table(overlay_skills.get("authored", {}), "overlay_skills.authored")
        for skill_name, state in sorted(authored.items()):
            _add_skill(
                package,
                root,
                skill_name,
                state,
                hosts,
                environment,
                local_allowed=True,
            )

    return package, "cursor" in hosts, source_attribute_dirs


def _validate_output_boundary(root: Path, path: Path) -> None:
    current = root
    for component in path.relative_to(root).parts:
        current /= component
        if current.is_symlink():
            raise MaterializerError(f"output boundary contains a symlink: {current}")
        if current.exists() and not current.is_dir():
            raise MaterializerError(
                f"output boundary contains a non-directory: {current}"
            )


def _validate_output_ancestors(path: Path) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            raise MaterializerError(
                f"output source root ancestor is a symlink: {current}"
            )
        if current.exists() and not current.is_dir():
            raise MaterializerError(
                f"output source root ancestor is not a directory: {current}"
            )


def _reject_existing_symlinks(path: Path, description: str) -> None:
    if not path.exists():
        return
    if path.is_symlink():
        raise MaterializerError(f"{description} is a symlink: {path}")
    for entry in path.rglob("*"):
        if entry.is_symlink():
            raise MaterializerError(
                f"{description} contains an output symlink: {entry}"
            )


def _remove_path(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _remove_path_best_effort(path: Path) -> None:
    with suppress(OSError):
        _remove_path(path)


def _encode_source_name(name: str) -> str:
    """Encode a generated directory name as an exact chezmoi source name."""
    literal = name.startswith(_SOURCE_ATTRIBUTE_PREFIXES)
    return f"exact_{'literal_' if literal else ''}{name}"


def _encode_source_file_name(name: str) -> str:
    """Encode a generated skill filename that chezmoi would interpret."""
    if name.endswith(".tmpl"):
        return f"literal_{name}.literal"
    if name.startswith(_SOURCE_ATTRIBUTE_PREFIXES):
        return f"literal_{name}"
    return name


def _mark_exact_tree(
    root: Path, source_attribute_dirs: set[Path] | None = None
) -> None:
    """Mark every generated directory as an exact chezmoi source boundary."""
    directories = sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: (
            len(path.relative_to(root).parts),
            path.relative_to(root).as_posix(),
        ),
        reverse=True,
    )
    targets: dict[Path, Path] = {}
    siblings: dict[Path, dict[str, Path]] = {}
    directory_set = set(directories)
    source_attribute_dirs = source_attribute_dirs or set()
    for path in directories:
        if path in source_attribute_dirs and path.name.startswith(
            _SOURCE_ATTRIBUTE_PREFIXES
        ):
            target_name = (
                path.name if path.name.startswith("exact_") else f"exact_{path.name}"
            )
        else:
            target_name = _encode_source_name(path.name)
        target = path.with_name(target_name)
        targets[path] = target
        names = siblings.setdefault(path.parent, {})
        if target.name in names:
            raise MaterializerError(
                f"exact output directory name collision: {names[target.name]} and {path}"
            )
        names[target.name] = path
        if os.path.lexists(target) and target not in directory_set:
            raise MaterializerError(f"exact output directory already exists: {target}")

    temporary_names: dict[Path, str] = {}
    temporary_token = uuid.uuid4().hex
    for index, path in enumerate(directories):
        temporary_name = f".materializer-exact-{temporary_token}-{index}"
        temporary = path.with_name(temporary_name)
        if os.path.lexists(temporary):
            raise MaterializerError(
                f"exact output temporary path already exists: {temporary}"
            )
        temporary_names[path] = temporary_name

    for path in directories:
        path.replace(path.with_name(temporary_names[path]))

    def temporary_path(path: Path) -> Path:
        original_current = root
        current = root
        for component in path.relative_to(root).parts:
            original_current /= component
            temporary_name = temporary_names.get(original_current)
            current /= temporary_name or component
        return current

    for path in directories:
        temporary_path(path).replace(temporary_path(path).with_name(targets[path].name))


def _replace_directory(
    staged: Path, destination: Path, backup: Path | None = None
) -> Path | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    if backup is None:
        backup = destination.with_name(f".{destination.name}.previous.{token}")
    staged_candidate = destination.with_name(f".{destination.name}.candidate.{token}")
    transaction = destination.with_name(f".{destination.name}.transaction.{token}")
    for path, description in (
        (backup, "publication backup"),
        (staged_candidate, "publication candidate"),
        (transaction, "publication journal"),
    ):
        if os.path.lexists(path):
            raise MaterializerError(f"{description} already exists: {path}")
    had_destination = os.path.lexists(destination)
    transaction.write_text(_PUBLICATION_JOURNAL, encoding="utf-8")
    candidate_staged = False
    published_backed_up = False
    candidate_published = False
    try:
        staged.replace(staged_candidate)
        candidate_staged = True
        if had_destination:
            destination.replace(backup)
            published_backed_up = True
        staged_candidate.replace(destination)
        candidate_published = True
        transaction.unlink()
    except BaseException:
        if candidate_published:
            _remove_path(destination)
        if published_backed_up and os.path.lexists(backup):
            backup.replace(destination)
        if candidate_staged and os.path.lexists(staged_candidate):
            _remove_path(staged_candidate)
        _remove_path_best_effort(transaction)
        raise
    return backup if had_destination else None


def _rollback_publication(published: Sequence[tuple[Path, Path | None]]) -> None:
    for destination, backup in reversed(published):
        _remove_path(destination)
        if backup is not None and os.path.lexists(backup):
            backup.replace(destination)


def _validate_declarations(
    capabilities: Mapping[str, object],
    plugins: Mapping[str, object],
    marketplaces: Mapping[str, object],
    skills: Mapping[str, object],
    overlay_skills: Mapping[str, object],
    acquired_sources: Mapping[str, object],
    working_tree: Path,
    environment: str,
) -> None:
    for raw_name, raw_definition in sorted(capabilities.items()):
        name = _name(raw_name, "capability")
        definition = _table(raw_definition, f"capability {name!r}")
        _validate_capability(
            name,
            definition,
            marketplaces,
            skills,
            overlay_skills,
            acquired_sources,
            working_tree,
            environment,
        )
    for raw_name, raw_definition in sorted(plugins.items()):
        name = _name(raw_name, "plugin")
        definition = _table(raw_definition, f"plugin {name!r}")
        _validate_plugin(
            name,
            definition,
            marketplaces,
            acquired_sources,
            working_tree,
            environment,
        )


def validate_plugin_references(payload: Mapping[str, object]) -> None:
    """Validate normalized plugin marketplace references without touching the filesystem."""
    _validate_plan_version(payload)
    bridge = _table(payload.get("plugin_bridge", {}), "plugin_bridge")
    marketplaces = _table(bridge.get("marketplaces", {}), "plugin_bridge.marketplaces")
    for raw_name, raw_definition in marketplaces.items():
        name = _name(raw_name, "marketplace")
        definition = _table(raw_definition, f"marketplace {name!r}")
        source_type = definition.get("source_type")
        if source_type not in {"generated", "host-provided", "internal", "public"}:
            raise MaterializerError(f"invalid marketplace source type: {source_type!r}")
        locator = definition.get("source_locator", "")
        if not isinstance(locator, str):
            raise MaterializerError(
                f"marketplace {name!r} source locator must be a string"
            )
        if source_type in {"internal", "public"} and not locator:
            raise MaterializerError(f"marketplace {name!r} source locator is required")
        if source_type == "host-provided" and locator:
            raise MaterializerError(
                f"marketplace {name!r} host-provided source cannot have a locator"
            )
        _hosts({}, definition)
        order = definition.get("order", 100)
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise MaterializerError(
                f"marketplace {name!r} order must be a non-negative integer"
            )

    for kind in ("capabilities", "plugins"):
        declarations = _table(bridge.get(kind, {}), f"plugin_bridge.{kind}")
        singular = kind[:-1]
        for raw_name, raw_definition in declarations.items():
            name = _name(raw_name, singular)
            definition = _table(raw_definition, f"{kind} {name!r}")
            _marketplace(
                marketplaces, definition.get("marketplace"), f"{singular} {name!r}"
            )


def _publish_staged(
    package_stage: Path,
    package_root: Path,
    cursor_stage: Path,
    cursor_root: Path,
) -> None:
    published: list[tuple[Path, Path | None]] = []
    try:
        published.append(
            (
                package_root,
                _replace_directory(package_stage, package_root),
            )
        )
        published.append(
            (
                cursor_root,
                _replace_directory(cursor_stage, cursor_root),
            )
        )
    except BaseException:
        _rollback_publication(published)
        raise
    for _, backup in published:
        if backup is not None:
            _remove_path_best_effort(backup)


def _publication_journal_paths(published: Path, transaction: Path) -> tuple[Path, Path]:
    prefix = f".{published.name}.transaction."
    if transaction.parent != published.parent or not transaction.name.startswith(
        prefix
    ):
        raise MaterializerError(f"unexpected publication journal: {transaction.name}")
    token = transaction.name[len(prefix) :]
    if not _PUBLICATION_TOKEN.fullmatch(token):
        raise MaterializerError(f"malformed publication journal: {transaction.name}")
    return (
        published.with_name(f".{published.name}.previous.{token}"),
        published.with_name(f".{published.name}.candidate.{token}"),
    )


def _is_publication_backup(path: Path, published: Path) -> bool:
    prefix = f".{published.name}.previous"
    for separator in (".", "-"):
        marker = f"{prefix}{separator}"
        if path.name.startswith(marker):
            return _PUBLICATION_TOKEN.fullmatch(path.name[len(marker) :]) is not None
    return False


def _recover_publication_transaction(published: Path, transaction: Path) -> None:
    if transaction.is_symlink() or not transaction.is_file():
        raise MaterializerError(
            f"publication journal must be a regular file: {transaction.name}"
        )
    if transaction.read_text(encoding="utf-8") != _PUBLICATION_JOURNAL:
        raise MaterializerError(f"malformed publication journal: {transaction.name}")
    backup, candidate = _publication_journal_paths(published, transaction)
    for path, description in (
        (backup, "publication backup"),
        (candidate, "publication candidate"),
    ):
        if path.is_symlink():
            raise MaterializerError(f"{description} is a symlink: {path.name}")
        if path.exists() and not path.is_dir():
            raise MaterializerError(f"{description} is not a directory: {path.name}")
        if path.exists():
            _validate_tree(path, description)
    if published.exists():
        _remove_path_best_effort(backup)
        _remove_path_best_effort(candidate)
    elif backup.exists():
        backup.replace(published)
        _remove_path_best_effort(candidate)
    else:
        _remove_path_best_effort(candidate)
    _remove_path_best_effort(transaction)


def _recover_publication(published: Path) -> None:
    if published.is_symlink():
        raise MaterializerError(f"published tree must not be a symlink: {published}")
    if published.exists() and not published.is_dir():
        raise MaterializerError(f"published tree must be a directory: {published}")
    prefix = f".{published.name}.transaction."
    for transaction in sorted(published.parent.glob(f"{prefix}*")):
        _recover_publication_transaction(published, transaction)

    if published.exists():
        for backup in published.parent.iterdir():
            if not _is_publication_backup(backup, published):
                continue
            if backup.is_symlink():
                raise MaterializerError(
                    f"publication backup is a symlink: {backup.name}"
                )
            _remove_path_best_effort(backup)


def materialize(payload: Mapping[str, object]) -> None:
    """Emit complete exact-owned generated packages and Cursor plugins."""
    validate_plugin_references(payload)
    bridge = _table(payload.get("plugin_bridge", {}), "plugin_bridge")
    marketplaces = _table(bridge.get("marketplaces", {}), "plugin_bridge.marketplaces")
    capabilities = _table(bridge.get("capabilities", {}), "plugin_bridge.capabilities")
    plugins = _table(bridge.get("plugins", {}), "plugin_bridge.plugins")
    skills = _table(payload.get("skills", {}), "skills")
    overlay_skills = _table(payload.get("overlay_skills", {}), "overlay_skills")
    acquired_sources = _table(payload.get("acquired_sources", {}), "acquired_sources")
    environment = _name(payload.get("environment"), "environment")
    working_tree = _path(payload.get("working_tree"), "working_tree", absolute=True)
    output = _path(
        payload.get("output_source_root"), "output_source_root", absolute=True
    )
    _validate_output_ancestors(output)
    output.mkdir(parents=True, exist_ok=True)
    _source_root(working_tree, "working tree")

    package_root = output / "dot_local/share/agent-plugins/marketplace/exact_plugins"
    cursor_root = output / "dot_cursor/plugins/exact_local"
    with _materialization_lock(output):
        _validate_output_boundary(output, package_root)
        _validate_output_boundary(output, cursor_root)
        _recover_publication(package_root)
        _recover_publication(cursor_root)
        _reject_existing_symlinks(package_root, "exact_plugins output")
        _reject_existing_symlinks(cursor_root, "exact_local output")

    for raw_source_id, raw_source in acquired_sources.items():
        source_id = _name(raw_source_id, "source")
        root = _path(raw_source, f"acquired source {source_id!r}", absolute=True)
        if root == working_tree or _is_relative_to(root, working_tree):
            raise MaterializerError(f"acquired source {source_id!r} must be acquired")
        _validate_tree(root, f"acquired source {source_id!r}")

    _validate_declarations(
        capabilities,
        plugins,
        marketplaces,
        skills,
        overlay_skills,
        acquired_sources,
        working_tree,
        environment,
    )

    staging_parent = Path(tempfile.mkdtemp(prefix=".plugin-materializer-", dir=output))
    try:
        package_stage = staging_parent / "exact_plugins"
        cursor_stage = staging_parent / "exact_local"
        package_stage.mkdir()
        cursor_stage.mkdir()
        packages: list[tuple[str, Path, bool, set[Path]]] = []
        for raw_name, raw_definition in sorted(capabilities.items()):
            name = _name(raw_name, "capability")
            definition = _table(raw_definition, f"capability {name!r}")
            if _enabled(definition, environment):
                package, has_cursor, source_attribute_dirs = _build_package(
                    name,
                    definition,
                    marketplaces,
                    skills,
                    overlay_skills,
                    acquired_sources,
                    working_tree,
                    package_stage,
                    environment,
                )
                packages.append((name, package, has_cursor, source_attribute_dirs))
        cursor_names: set[str] = set()
        cursor_source_attribute_dirs: dict[Path, set[Path]] = {}
        for name, package, has_cursor, source_attribute_dirs in packages:
            if has_cursor:
                cursor_stage_path = cursor_stage / f"exact_{name}"
                _copy_tree(
                    package / "cursor",
                    cursor_stage_path,
                    "cursor wrapper source",
                )
                cursor_source_attribute_dirs[cursor_stage_path] = {
                    cursor_stage_path / path.relative_to(package / "cursor")
                    for path in source_attribute_dirs
                    if _is_relative_to(path, package / "cursor")
                }
                cursor_names.add(name)

        for raw_name, raw_definition in sorted(plugins.items()):
            name = _name(raw_name, "plugin")
            definition = _table(raw_definition, f"plugin {name!r}")
            marketplace = _marketplace(
                marketplaces, definition.get("marketplace"), f"plugin {name!r}"
            )
            if not _enabled(definition, environment) or "cursor" not in _hosts(
                definition, marketplace
            ):
                continue
            if name in cursor_names:
                raise MaterializerError(f"duplicate cursor plugin name: {name!r}")
            cursor_source_id = definition.get("cursor_source_id")
            if cursor_source_id is not None:
                cursor_source = _acquired_source(
                    {
                        "source_id": cursor_source_id,
                        "source_root": definition.get("cursor_source_root", "."),
                    },
                    acquired_sources,
                    working_tree,
                )
            else:
                cursor_source = _source(
                    working_tree,
                    definition.get("cursor_source_dir"),
                    f"cursor plugin source for {name!r}",
                )
            assert cursor_source is not None
            cursor_stage_path = cursor_stage / f"exact_{name}"
            cursor_attribute_dirs: set[Path] = set()
            _copy_tree(
                cursor_source,
                cursor_stage_path,
                "cursor plugin source",
                cursor_attribute_dirs,
            )
            cursor_source_attribute_dirs[cursor_stage_path] = cursor_attribute_dirs
            cursor_names.add(name)

        for package in package_stage.iterdir():
            source_attribute_dirs = next(
                source_dirs
                for package_name, package_path, _, source_dirs in packages
                if package_path == package
            )
            _mark_exact_tree(package, source_attribute_dirs)
        for plugin in cursor_stage.iterdir():
            _mark_exact_tree(plugin, cursor_source_attribute_dirs.get(plugin))

        with _materialization_lock(output):
            _validate_output_boundary(output, package_root)
            _validate_output_boundary(output, cursor_root)
            _recover_publication(package_root)
            _recover_publication(cursor_root)
            _reject_existing_symlinks(package_root, "exact_plugins output")
            _reject_existing_symlinks(cursor_root, "exact_local output")
            _publish_staged(
                package_stage,
                package_root,
                cursor_stage,
                cursor_root,
            )
    finally:
        shutil.rmtree(staging_parent, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Read one normalized declaration as JSON from stdin and materialize it."""
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments not in ((), ("--validate-references",)):
        print("plugin-materializer: unsupported arguments", file=sys.stderr)
        return 2
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError) as error:
        print(f"plugin-materializer: invalid JSON: {error}", file=sys.stderr)
        return 1
    if not isinstance(payload, Mapping):
        print("plugin-materializer: input must be a JSON object", file=sys.stderr)
        return 1
    try:
        if arguments == ("--validate-references",):
            validate_plugin_references(payload)
        else:
            materialize(payload)
    except (MaterializerError, OSError) as error:
        print(f"plugin-materializer: {error}", file=sys.stderr)
        return 1
    return 0


__all__ = ["MaterializerError", "main", "materialize", "validate_plugin_references"]


if __name__ == "__main__":
    sys.exit(main())
