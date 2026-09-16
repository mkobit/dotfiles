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
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Callable,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    cast,
)

if TYPE_CHECKING:
    from pathlib import Path


class Selection(NamedTuple):
    src: str
    dest: str


class FilterError(Exception):
    """Raised when the archive or arguments are invalid."""


class PackageCleanup(NamedTuple):
    stable_key: str
    root: str
    expected_files: tuple[str, ...]
    preserved_directories: tuple[str, ...]


class ManagedPluginResource(NamedTuple):
    kind: str
    host: str
    marketplace: str
    resource_id: str
    order: int
    fingerprint: str
    install: tuple[str, ...]
    update: tuple[str, ...]
    enable: tuple[str, ...]
    uninstall: tuple[str, ...]
    status: tuple[str, ...]
    verify: tuple[str, ...]
    expected_skills: tuple[str, ...]
    adopt: bool
    package_cleanup: PackageCleanup | None


class PluginPlan(NamedTuple):
    version: int
    resources: tuple[ManagedPluginResource, ...]
    skill_mappings: tuple[tuple[str, str, str, str], ...]
    legacy_cleanup: object
    owned_removals: tuple[PluginOperation, ...] | None
    generated_marketplace_root: str | None


class PluginOperation(NamedTuple):
    action: str
    kind: str
    host: str
    resource_id: str
    argv: tuple[str, ...]


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise FilterError(f"{field} must be a list of strings")
    return tuple(item for item in value if isinstance(item, str))


def _package_cleanup(
    raw: object, *, generated_marketplace_root: str | None = None
) -> PackageCleanup | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FilterError("package cleanup must be an object")
    cleanup = cast(Dict[str, object], raw)
    stable_key = cleanup.get("stable_key")
    root = cleanup.get("root")
    expected_files = cleanup.get("expected_files")
    preserved_directories = cleanup.get("preserved_directories", ())
    if not isinstance(stable_key, str) or not stable_key:
        raise FilterError("package cleanup stable_key must be a non-empty string")
    if (
        stable_key in (".", "..")
        or "/" in stable_key
        or "\\" in stable_key
        or "\0" in stable_key
    ):
        raise FilterError("package cleanup stable_key must be a simple path name")
    if not isinstance(root, str) or not root:
        raise FilterError("package cleanup root must be a non-empty string")
    if not os.path.isabs(root) or "\0" in root:
        raise FilterError("package cleanup root must be absolute")
    if not isinstance(expected_files, (list, tuple)) or not all(
        isinstance(entry, str) for entry in expected_files
    ):
        raise FilterError("package cleanup expected_files must be a list of strings")
    if not isinstance(preserved_directories, (list, tuple)) or not all(
        isinstance(entry, str) for entry in preserved_directories
    ):
        raise FilterError(
            "package cleanup preserved_directories must be a list of strings"
        )
    entries = tuple(cast(str, entry) for entry in expected_files)
    preserved = tuple(cast(str, entry) for entry in preserved_directories)
    for entry in (*entries, *preserved):
        parts = entry.split("/")
        if (
            not entry
            or "\0" in entry
            or "\\" in entry
            or os.path.isabs(entry)
            or any(part in ("", ".", "..") for part in parts)
        ):
            raise FilterError(f"package cleanup expected file is unsafe: {entry!r}")
    if len(entries) != len(set(entries)):
        raise FilterError("package cleanup expected_files contain a duplicate entry")
    if len(preserved) != len(set(preserved)):
        raise FilterError(
            "package cleanup preserved_directories contain a duplicate entry"
        )
    sorted_entries = sorted(entries)
    for parent, child in zip(sorted_entries, sorted_entries[1:]):
        if child.startswith(f"{parent}/"):
            raise FilterError(
                "package cleanup expected_files contain a file/directory conflict"
            )
    for preserved_root in preserved:
        if preserved_root in entries or any(
            preserved_root.startswith(f"{entry}/")
            or entry.startswith(f"{preserved_root}/")
            for entry in entries
        ):
            raise FilterError(
                "package cleanup file and preserved directory inventories conflict"
            )
    if generated_marketplace_root is not None:
        if (
            not os.path.isabs(generated_marketplace_root)
            or "\0" in generated_marketplace_root
        ):
            raise FilterError("generated marketplace root must be absolute")
        expected_root = os.path.join(generated_marketplace_root, "plugins", stable_key)
        if root != os.path.normpath(root) or root != expected_root:
            raise FilterError(
                "package cleanup root is outside generated marketplace root"
            )
    return PackageCleanup(stable_key, root, entries, preserved)


def _derived_enable_command(install: tuple[str, ...]) -> tuple[str, ...]:
    """Derive the generic bridge enable operation for legacy v2 plans."""
    if len(install) >= 4 and install[1].startswith("plugin-"):
        return (install[0], "plugin-enable", *install[2:])
    if len(install) >= 4 and install[1:3] == ("plugin", "install"):
        return (install[0], "plugin", "enable", *install[3:])
    return ()


def _plugin_resource(
    raw: object, *, version: int, generated_marketplace_root: str | None = None
) -> ManagedPluginResource:
    if not isinstance(raw, dict):
        raise FilterError("plugin plan resources must be objects")
    resource = cast(Dict[str, object], raw)
    try:
        kind = resource["kind"]
        host = resource["host"]
        resource_id = resource["id"]
        fingerprint = resource["fingerprint"]
        marketplace = resource.get("marketplace", "")
        order = resource.get("order", 0)
        install = _string_tuple(resource["install"], "plugin resource install argv")
        update = _string_tuple(
            resource.get("update", install), "plugin resource update argv"
        )
        enable = _string_tuple(
            resource.get("enable", _derived_enable_command(install)),
            "plugin resource enable argv",
        )
        uninstall = _string_tuple(
            resource["uninstall"], "plugin resource uninstall argv"
        )
        status = _string_tuple(
            resource.get("status", ()), "plugin resource status argv"
        )
        verify = _string_tuple(
            resource.get("verify", ()), "plugin resource verify argv"
        )
        expected_skills = _string_tuple(
            resource.get("expected_skills", ()), "plugin resource expected skills"
        )
        adopt = resource.get("adopt", False)
        package_cleanup = resource.get("package_cleanup")
    except (KeyError, TypeError) as error:
        raise FilterError(f"invalid plugin plan resource: {error}") from error
    if not (
        isinstance(kind, str)
        and isinstance(host, str)
        and isinstance(marketplace, str)
        and isinstance(resource_id, str)
        and isinstance(fingerprint, str)
    ):
        raise FilterError("plugin resource fields must be strings")
    if not isinstance(order, int) or isinstance(order, bool):
        raise FilterError("plugin resource order must be an integer")
    if kind not in ("marketplace", "plugin"):
        raise FilterError(f"unsupported plugin resource kind {kind!r}")
    if not isinstance(adopt, bool):
        raise FilterError("plugin resource adopt marker must be a boolean")
    if adopt and kind != "plugin":
        raise FilterError("only plugin resources can be adopted")
    if adopt and not verify:
        raise FilterError("adopted plugin resource must provide verification argv")
    if package_cleanup is not None and kind != "plugin":
        raise FilterError("only plugin resources can have package cleanup")
    parsed_package_cleanup = _package_cleanup(
        package_cleanup,
        generated_marketplace_root=(
            generated_marketplace_root if kind == "plugin" else None
        ),
    )
    if kind == "plugin" and not adopt and not status and version == 1:
        raise FilterError("plugin resource must provide status argv")
    if kind == "marketplace" and not marketplace:
        # Version 1 marketplace plans used their id as the marketplace identity.
        marketplace = resource_id
    elif kind == "plugin" and not marketplace and "@" in resource_id:
        # Version 1 ownership and plans did not carry marketplace separately.
        # Recover the conventional marketplace suffix where possible.
        marketplace = resource_id.rsplit("@", 1)[1]
    return ManagedPluginResource(
        kind,
        host,
        marketplace,
        resource_id,
        order,
        fingerprint,
        install,
        update,
        enable if version >= 2 else (),
        uninstall,
        status,
        verify,
        expected_skills,
        adopt,
        parsed_package_cleanup,
    )


def _owned_removal_preview(raw: object) -> PluginOperation:
    if not isinstance(raw, dict):
        raise FilterError("owned removal previews must be objects")
    removal = cast(Dict[str, object], raw)
    try:
        action = removal["action"]
        kind = removal["kind"]
        host = removal["host"]
        resource_id = removal["id"]
        argv = _string_tuple(removal["argv"], "owned removal preview argv")
    except (KeyError, TypeError) as error:
        raise FilterError(f"invalid owned removal preview: {error}") from error
    if action != "uninstall":
        raise FilterError("owned removal preview action must be uninstall")
    if not (
        isinstance(action, str)
        and isinstance(kind, str)
        and isinstance(host, str)
        and isinstance(resource_id, str)
    ):
        raise FilterError("owned removal preview fields must be strings")
    return PluginOperation(action, kind, host, resource_id, argv)


def parse_plugin_plan(content: str) -> PluginPlan:
    """Parse the rendered plugin desired-state plan."""
    import json

    try:
        raw = json.loads(content)
    except (TypeError, ValueError) as error:
        raise FilterError(f"invalid plugin plan JSON: {error}") from error
    if not isinstance(raw, dict) or raw.get("version") not in (1, 2):
        raise FilterError("plugin plan must be a version 1 or 2 object")
    version = int(raw["version"])
    generated_marketplace_root = raw.get("generated_marketplace_root")
    if generated_marketplace_root is not None and not isinstance(
        generated_marketplace_root, str
    ):
        raise FilterError("generated marketplace root must be a string")
    if generated_marketplace_root is not None and not os.path.isabs(
        generated_marketplace_root
    ):
        raise FilterError("generated marketplace root must be absolute")
    resources = tuple(
        _plugin_resource(
            item,
            version=version,
            generated_marketplace_root=generated_marketplace_root,
        )
        for item in raw.get("resources", ())
    )
    resource_identities = [_identity(resource) for resource in resources]
    if len(resource_identities) != len(set(resource_identities)):
        raise FilterError("duplicate desired resource identity")
    mappings = []
    for item in raw.get("skill_mappings", ()):
        if not isinstance(item, dict):
            raise FilterError("skill mappings must be objects")
        try:
            mappings.append(
                (
                    item["legacy_root"],
                    item["host"],
                    item["plugin"],
                    item["skill"],
                )
            )
        except KeyError as error:
            raise FilterError(f"invalid skill mapping: {error}") from error
    legacy_roots = [mapping[0] for mapping in mappings]
    replacements = [mapping[1:] for mapping in mappings]
    if len(legacy_roots) != len(set(legacy_roots)) or len(replacements) != len(
        set(replacements)
    ):
        raise FilterError("ambiguous skill mapping")
    plugin_skills = {
        (resource.host, resource.resource_id): set(resource.expected_skills)
        for resource in resources
        if resource.kind == "plugin"
    }
    for legacy_root, host, plugin_id, skill in mappings:
        if skill not in plugin_skills.get((host, plugin_id), set()):
            raise FilterError(
                f"legacy cleanup mapping for {legacy_root!r} has no desired plugin skill"
            )
    raw_owned_removals = raw.get("owned_removals")
    if raw_owned_removals is None:
        owned_removals = None
    elif not isinstance(raw_owned_removals, list):
        raise FilterError("owned removal previews must be a list")
    else:
        owned_removals = tuple(
            _owned_removal_preview(item) for item in raw_owned_removals
        )
    return PluginPlan(
        version,
        resources,
        tuple(sorted(mappings)),
        raw.get("legacy_cleanup"),
        owned_removals,
        generated_marketplace_root,
    )


def parse_plugin_ownership(content: str) -> tuple[ManagedPluginResource, ...]:
    """Parse resources recorded by an earlier successful reconciliation."""
    import json

    if not content:
        return ()
    try:
        raw = json.loads(content)
    except (KeyError, TypeError, ValueError) as error:
        raise FilterError(f"invalid plugin ownership JSON: {error}") from error
    if not isinstance(raw, dict) or raw.get("version") not in (1, 2):
        raise FilterError("plugin ownership must be a version 1 or 2 object")
    version = int(raw["version"])
    raw_resources = raw.get("resources")
    if not isinstance(raw_resources, list):
        raise FilterError("plugin ownership resources must be a list")
    resources = []
    for item in raw_resources:
        if not isinstance(item, dict):
            raise FilterError("plugin ownership resources must be objects")
        try:
            resources.append(_ownership_resource(item, version=version))
        except (KeyError, TypeError) as error:
            raise FilterError(f"invalid plugin ownership resource: {error}") from error
    return tuple(resources)


def _ownership_resource(
    item: dict[str, object], *, version: int
) -> ManagedPluginResource:
    """Decode v1 ownership and normalize it to the v2 in-memory shape."""
    kind = item["kind"]
    host = item["host"]
    resource_id = item["id"]
    fingerprint = item["fingerprint"]
    marketplace = item.get("marketplace", "")
    order = item.get("order", 0)
    uninstall = _string_tuple(item["uninstall"], "plugin ownership uninstall argv")
    if not all(
        isinstance(value, str)
        for value in (kind, host, resource_id, fingerprint, marketplace)
    ):
        raise FilterError("plugin ownership resource fields must be strings")
    if not isinstance(order, int) or isinstance(order, bool):
        raise FilterError("plugin ownership resource order must be an integer")
    if kind not in ("marketplace", "plugin"):
        raise FilterError(f"unsupported plugin ownership resource kind {kind!r}")
    if kind == "marketplace" and not marketplace:
        # Version 1 marketplace ownership used its id as the marketplace identity.
        marketplace = resource_id
    elif kind == "plugin" and not marketplace and "@" in resource_id:
        marketplace = resource_id.rsplit("@", 1)[1]
    package_cleanup = _package_cleanup(item.get("package_cleanup"))
    return ManagedPluginResource(
        kind,
        host,
        marketplace,
        resource_id,
        order,
        fingerprint,
        (),
        (),
        (),
        uninstall,
        (),
        (),
        (),
        False,
        package_cleanup,
    )


def _identity(resource: ManagedPluginResource) -> tuple[str, str, str, str]:
    return (resource.kind, resource.host, resource.marketplace, resource.resource_id)


def _canonical_removal_operations(
    operations: Iterable[PluginOperation],
) -> tuple[PluginOperation, ...]:
    """Compare removal previews as an exact multiset, independent of order."""
    return tuple(
        sorted(
            operations,
            key=lambda operation: (
                operation.action,
                operation.kind,
                operation.host,
                operation.resource_id,
                operation.argv,
            ),
        )
    )


def plan_plugin_operations(
    desired: PluginPlan, owned: Iterable[ManagedPluginResource]
) -> tuple[PluginOperation, ...]:
    """Return stable install and owned-resource uninstall operations."""
    owned_resources = tuple(owned)
    owned_by_identity = {_identity(resource): resource for resource in owned_resources}
    desired_identities = {_identity(resource) for resource in desired.resources}
    kind_order = {"marketplace": 0, "plugin": 1}
    installs = []
    for resource in sorted(
        desired.resources,
        key=lambda resource: (
            kind_order[resource.kind],
            getattr(resource, "order", 0),
            resource.marketplace,
            resource.host,
            resource.resource_id,
        ),
    ):
        prior = owned_by_identity.get(_identity(resource))
        if resource.kind == "plugin" and resource.status:
            installs.append(
                PluginOperation(
                    "preflight",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.status,
                )
            )
        if prior is not None and prior.fingerprint != resource.fingerprint:
            installs.append(
                PluginOperation(
                    "update",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.update,
                )
            )
        elif prior is None:
            if resource.adopt:
                installs.append(
                    PluginOperation(
                        "adopt",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.verify,
                    )
                )
            else:
                installs.append(
                    PluginOperation(
                        "install",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.install,
                    )
                )
    obsolete = (
        resource
        for resource in owned_resources
        if _identity(resource) not in desired_identities
    )
    uninstalls = tuple(
        PluginOperation(
            "uninstall",
            resource.kind,
            resource.host,
            resource.resource_id,
            resource.uninstall,
        )
        for resource in sorted(
            obsolete,
            key=lambda resource: (
                -getattr(resource, "order", 0),
                -kind_order[resource.kind],
                resource.marketplace,
                resource.host,
                resource.resource_id,
            ),
        )
    )
    return tuple(installs) + uninstalls


def _render_plugin_ownership(resources: Iterable[ManagedPluginResource]) -> str:
    import json

    records = []
    for resource in sorted(
        resources,
        key=lambda resource: (
            resource.order,
            resource.kind,
            resource.marketplace,
            resource.host,
            resource.resource_id,
        ),
    ):
        record = {
            "kind": resource.kind,
            "host": resource.host,
            "marketplace": resource.marketplace,
            "id": resource.resource_id,
            "order": resource.order,
            "fingerprint": resource.fingerprint,
            "enable": list(resource.enable),
            "uninstall": list(resource.uninstall),
        }
        if resource.package_cleanup is not None:
            record["package_cleanup"] = {
                "stable_key": resource.package_cleanup.stable_key,
                "root": resource.package_cleanup.root,
                "expected_files": list(resource.package_cleanup.expected_files),
                "preserved_directories": list(
                    resource.package_cleanup.preserved_directories
                ),
            }
        records.append(record)
    return (
        json.dumps(
            {"version": 2, "resources": records},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _legacy_cleanup_fields(
    raw: object,
) -> tuple[dict[str, object], str, str, str]:
    if not isinstance(raw, dict):
        raise FilterError("legacy_cleanup must be an object")
    cleanup = cast(Dict[str, object], raw)
    try:
        destination = cleanup["dest_dir"]
        state_manifest = cleanup["state_manifest"]
        desired_manifest = cleanup["desired_manifest"]
    except KeyError as error:
        raise FilterError(f"invalid legacy_cleanup plan: {error}") from error
    if not (
        isinstance(destination, str)
        and isinstance(state_manifest, str)
        and isinstance(desired_manifest, str)
    ):
        raise FilterError("legacy_cleanup paths and manifest must be strings")
    return cleanup, destination, state_manifest, desired_manifest


def _validate_legacy_cleanup_plan(dest_dir: Path, desired: PluginPlan) -> None:
    """Require every deferred legacy removal to name a verified replacement."""
    from pathlib import Path

    cleanup = desired.legacy_cleanup
    if cleanup is None:
        if desired.skill_mappings:
            raise FilterError("legacy cleanup mapping has no cleanup root")
        return
    cleanup, cleanup_destination, state_manifest, desired_manifest = (
        _legacy_cleanup_fields(cleanup)
    )
    destination = Path(dest_dir)
    if Path(cleanup_destination) != destination:
        raise FilterError("legacy cleanup destination does not match reconciliation")
    manifest = validate_state_manifest_path(destination, Path(state_manifest))
    desired_roots = parse_skill_root_manifest(desired_manifest, allow_duplicates=True)
    validate_skill_root_manifest(destination, desired_roots)
    prior_roots = ()
    if manifest.exists():
        prior_roots = parse_skill_root_manifest(manifest.read_text(encoding="utf-8"))
        validate_skill_root_manifest(destination, prior_roots)
    cleanup_roots = set(prior_roots) - set(desired_roots)
    direct_roots = cleanup.get("direct_roots", [])
    if not isinstance(direct_roots, list) or not all(
        isinstance(root, str) for root in direct_roots
    ):
        raise FilterError("legacy direct cleanup roots must be a list of paths")
    direct_root_set = set(direct_roots)
    if len(direct_root_set) != len(direct_roots):
        raise FilterError("legacy direct cleanup roots contain a duplicate entry")
    expected_direct_roots = {
        root
        for root in cleanup_roots
        if _skill_root_parent(root) == ".gemini/antigravity-cli/skills"
    }
    if direct_root_set != expected_direct_roots:
        raise FilterError(
            "legacy direct cleanup roots do not match Antigravity cleanup roots"
        )
    mappings_by_root = {mapping[0]: mapping[1:] for mapping in desired.skill_mappings}
    if set(mappings_by_root) != cleanup_roots - direct_root_set:
        raise FilterError("legacy cleanup mapping does not match cleanup roots")
    plugins = {
        (resource.host, resource.resource_id): set(resource.expected_skills)
        for resource in desired.resources
        if resource.kind == "plugin"
    }
    for root, (host, plugin_id, skill) in mappings_by_root.items():
        if skill not in plugins.get((host, plugin_id), set()):
            raise FilterError(
                f"legacy cleanup mapping for {root!r} has no desired plugin skill"
            )


def _cleanup_generated_package(
    generated_marketplace_root: str, resource: ManagedPluginResource
) -> None:
    """Prune stale files from one validated generated plugin package."""
    from pathlib import Path

    cleanup = resource.package_cleanup
    if cleanup is None:
        return
    generated_root = Path(generated_marketplace_root)
    package_root = Path(cleanup.root)
    expected_root = generated_root / "plugins" / cleanup.stable_key
    if not generated_root.is_absolute() or package_root != expected_root:
        raise FilterError("package cleanup root is outside generated marketplace root")

    for ancestor in (package_root, *package_root.parents):
        if ancestor.is_symlink():
            raise FilterError("package cleanup path contains a symlink")
    if not package_root.exists():
        return
    if not package_root.is_dir():
        raise FilterError("package cleanup root is not a directory")

    expected_files = set(cleanup.expected_files)
    preserved_directories = set(cleanup.preserved_directories)

    def prune(directory: Path) -> None:
        for entry in os.scandir(directory):
            path = Path(entry.path)
            relative = path.relative_to(package_root).as_posix()
            if relative in preserved_directories:
                if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                    raise FilterError(
                        "package cleanup preserved path is not a directory: "
                        f"{relative!r}"
                    )
                continue
            if entry.is_symlink():
                if relative in expected_files:
                    raise FilterError(
                        f"package cleanup expected file is a symlink: {relative!r}"
                    )
                path.unlink()
                continue
            if entry.is_dir(follow_symlinks=False):
                if relative in expected_files:
                    raise FilterError(
                        f"package cleanup expected file is a directory: {relative!r}"
                    )
                prune(path)
                try:
                    path.rmdir()
                except OSError:
                    pass
                continue
            if not entry.is_file(follow_symlinks=False):
                raise FilterError(
                    f"package cleanup encountered special file: {relative!r}"
                )
            if relative not in expected_files:
                path.unlink()

    prune(package_root)


def reconcile_plugins(
    dest_dir: Path,
    ownership_file: Path,
    desired: PluginPlan,
    execute: Callable[[PluginOperation], Iterable[str]],
    cleanup_legacy: Callable[[object], None],
) -> tuple[ManagedPluginResource, ...]:
    """Converge managed plugin resources without touching unmanaged resources."""
    import json
    from pathlib import Path

    destination = Path(dest_dir)
    ownership_path = validate_state_manifest_path(destination, ownership_file)
    _validate_legacy_cleanup_plan(destination, desired)
    owned = ()
    ownership_version = 2
    if ownership_path.exists():
        ownership_content = ownership_path.read_text(encoding="utf-8")
        owned = parse_plugin_ownership(ownership_content)
        try:
            ownership_version = json.loads(ownership_content).get("version", 1)
        except (TypeError, ValueError):
            ownership_version = 1
    operations = plan_plugin_operations(desired, owned)
    owned_removals = tuple(
        operation for operation in operations if operation.action == "uninstall"
    )
    if desired.owned_removals is not None and _canonical_removal_operations(
        desired.owned_removals
    ) != _canonical_removal_operations(owned_removals):
        raise FilterError("owned removal preview does not match current ownership")
    managed_by_identity = {_identity(resource): resource for resource in owned}
    desired_by_identity = {
        _identity(resource): resource for resource in desired.resources
    }

    durable_by_identity = dict(managed_by_identity)

    def checkpoint(
        resources: Mapping[tuple[str, str, str], ManagedPluginResource],
    ) -> None:
        _replace_manifest_atomically(
            ownership_path, _render_plugin_ownership(resources.values())
        )

    def verify(resource: ManagedPluginResource) -> None:
        actual_skills = tuple(
            execute(
                PluginOperation(
                    "verify",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.verify,
                )
            )
        )
        if tuple(sorted(actual_skills)) != tuple(sorted(resource.expected_skills)):
            raise FilterError(
                f"plugin {resource.resource_id!r} on {resource.host!r} has "
                f"skills {actual_skills!r}, expected {resource.expected_skills!r}"
            )

    # Desired resources are fully converged before any removal is attempted.
    for resource in desired.resources:
        identity = _identity(resource)
        prior = managed_by_identity.get(identity)
        if resource.kind == "marketplace":
            if prior is None:
                execute(
                    PluginOperation(
                        "install",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.install,
                    )
                )
                managed_by_identity[identity] = resource
                durable_by_identity[identity] = resource
                checkpoint(durable_by_identity)
            elif prior.fingerprint != resource.fingerprint:
                execute(
                    PluginOperation(
                        "update",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.update,
                    )
                )
                managed_by_identity[identity] = resource
                durable_by_identity[identity] = resource
                checkpoint(durable_by_identity)
            continue

        occupied = ()
        if resource.status:
            occupied = tuple(
                execute(
                    PluginOperation(
                        "preflight",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.status,
                    )
                )
            )
        installed = "installed" in occupied

        if prior is None:
            if resource.adopt:
                # Explicit adoption keeps the v1 callback contract.  The host
                # command must return the same strict verification payload.
                output = tuple(
                    execute(
                        PluginOperation(
                            "adopt",
                            resource.kind,
                            resource.host,
                            resource.resource_id,
                            resource.verify,
                        )
                    )
                )
                if tuple(sorted(output)) != tuple(sorted(resource.expected_skills)):
                    raise FilterError(
                        f"plugin {resource.resource_id!r} on {resource.host!r} has skills "
                        f"{output!r}, expected {resource.expected_skills!r}"
                    )
            elif not installed:
                execute(
                    PluginOperation(
                        "install",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.install,
                    )
                )
            if resource.enable and (not installed or "enabled" not in occupied):
                execute(
                    PluginOperation(
                        "enable",
                        resource.kind,
                        resource.host,
                        resource.resource_id,
                        resource.enable,
                    )
                )
            if not resource.adopt:
                verify(resource)
            if resource.package_cleanup is not None:
                if desired.generated_marketplace_root is None:
                    raise FilterError(
                        "package cleanup requires generated marketplace root"
                    )
                _cleanup_generated_package(desired.generated_marketplace_root, resource)
            managed_by_identity[identity] = resource
            durable_by_identity[identity] = resource
            checkpoint(durable_by_identity)
            continue

        changed = prior.fingerprint != resource.fingerprint
        if not installed:
            execute(
                PluginOperation(
                    "install",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.install,
                )
            )
        elif changed:
            execute(
                PluginOperation(
                    "update",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.update,
                )
            )
        if resource.enable and (not installed or changed or "enabled" not in occupied):
            execute(
                PluginOperation(
                    "enable",
                    resource.kind,
                    resource.host,
                    resource.resource_id,
                    resource.enable,
                )
            )
        verify(resource)
        if resource.package_cleanup is not None:
            if desired.generated_marketplace_root is None:
                raise FilterError("package cleanup requires generated marketplace root")
            _cleanup_generated_package(desired.generated_marketplace_root, resource)
        managed_by_identity[identity] = resource
        durable_by_identity[identity] = resource
        checkpoint(durable_by_identity)

    if desired.legacy_cleanup is not None:
        cleanup_legacy(desired.legacy_cleanup)

    # Removal is deliberately last, and each successful removal is durable.
    obsolete = [
        resource
        for identity, resource in managed_by_identity.items()
        if identity not in desired_by_identity
    ]
    kind_order = {"marketplace": 0, "plugin": 1}
    for resource in sorted(
        obsolete,
        key=lambda item: (
            -kind_order[item.kind],
            -item.order,
            item.host,
            item.resource_id,
        ),
    ):
        execute(
            PluginOperation(
                "uninstall",
                resource.kind,
                resource.host,
                resource.resource_id,
                resource.uninstall,
            )
        )
        managed_by_identity.pop(_identity(resource), None)
        durable_by_identity.pop(_identity(resource), None)
        checkpoint(durable_by_identity)

    if ownership_version != 2:
        durable_by_identity = dict(managed_by_identity)
        checkpoint(durable_by_identity)

    if (
        not ownership_path.exists()
        and (
            desired.generated_marketplace_root is not None
            or desired.legacy_cleanup is not None
            or desired.resources
        )
    ) or durable_by_identity != managed_by_identity:
        checkpoint(managed_by_identity)

    return tuple(desired.resources)


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
        expected_parent = resolved_destination / parent
        resolved_entry = (destination / entry).resolve()
        if resolved_parent != expected_parent:
            raise FilterError(
                f"allowed skill root {parent!r} is a symlink or resolves outside its destination-relative path"
            )
        if resolved_entry.parent != resolved_parent:
            raise FilterError(
                f"skill root {entry!r} escapes its allowed skills directory"
            )
        validated.append(destination / entry)
    return tuple(validated)


def validate_state_manifest_path(dest_dir: Path, state_manifest: Path) -> Path:
    """Reject state manifests outside their canonical destination state path."""
    from pathlib import Path

    destination = Path(dest_dir)
    manifest = Path(state_manifest)
    if not destination.is_absolute():
        raise FilterError("destination directory must be absolute")
    if not manifest.is_absolute():
        raise FilterError("state manifest path must be absolute")
    resolved_destination = destination.resolve()
    state_root = destination / ".local/state/dotfiles"
    expected_state_root = resolved_destination / ".local/state/dotfiles"
    try:
        relative_manifest = manifest.relative_to(state_root)
    except ValueError as error:
        raise FilterError(
            f"state manifest must be strictly beneath {expected_state_root}"
        ) from error
    if not relative_manifest.parts:
        raise FilterError(
            f"state manifest must be strictly beneath {expected_state_root}"
        )
    resolved_state_root = state_root.resolve()
    resolved_manifest = manifest.resolve()
    expected_manifest = expected_state_root / relative_manifest
    if (
        resolved_state_root != expected_state_root
        or resolved_manifest != expected_manifest
    ):
        raise FilterError(
            "state manifest path must not contain symlinks or redirected ancestors"
        )
    return manifest


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
    manifest = validate_state_manifest_path(destination, state_manifest)
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
        for stale, _stale_path in stale_roots:
            (stale_path,) = validate_skill_root_manifest(destination, (stale,))
            if stale_path.is_symlink():
                raise FilterError(f"refusing to delete symlink skill root {stale!r}")
            if stale_path.exists() and not stale_path.is_dir():
                raise FilterError(
                    f"refusing to delete non-directory skill root {stale!r}"
                )
            if stale_path.exists():
                shutil.rmtree(stale_path)

    rendered = "".join(f"{entry}\n" for entry in desired)
    validate_state_manifest_path(destination, manifest)
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


def _parse_reconcile_plugins_args(argv: Iterable[str]) -> argparse.Namespace:
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog="skill-filter reconcile-plugins",
        description="converge managed user-scoped agent plugins from a JSON plan",
    )
    parser.add_argument(
        "--dest-dir",
        required=True,
        type=Path,
        help="chezmoi destination directory",
    )
    parser.add_argument(
        "--ownership-file",
        required=True,
        type=Path,
        help="runtime ownership record under .local/state/dotfiles",
    )
    return parser.parse_args(list(argv))


def _execute_plugin_command(operation: PluginOperation) -> tuple[str, ...]:
    import json
    import subprocess

    if not operation.argv:
        raise FilterError(
            f"{operation.action} command is missing for {operation.resource_id!r}"
        )
    completed = subprocess.run(
        operation.argv,
        check=True,
        capture_output=operation.action in ("verify", "adopt", "preflight", "status"),
        text=True,
    )
    if operation.action not in ("verify", "adopt", "preflight", "status"):
        return ()
    if operation.action in ("preflight", "status") and not completed.stdout:
        return ()
    try:
        output = json.loads(completed.stdout)
        if operation.action in ("preflight", "status"):
            installed = output["installed"]
            if not isinstance(installed, bool):
                raise TypeError("installed must be a boolean")
            if not installed:
                return ()
            enabled = output.get("enabled", False)
            if not isinstance(enabled, bool):
                raise TypeError("enabled must be a boolean")
            return ("installed", "enabled") if enabled else ("installed",)
        skills = output["skills"] if isinstance(output, dict) else output
    except (KeyError, TypeError, ValueError) as error:
        raise FilterError(
            f"invalid skill verification output for {operation.resource_id!r}"
        ) from error
    if not isinstance(skills, list) or not all(
        isinstance(skill, str) for skill in skills
    ):
        raise FilterError(
            f"invalid skill verification output for {operation.resource_id!r}"
        )
    return tuple(skills)


def _cleanup_legacy_skill_roots(cleanup_plan: object) -> None:
    from pathlib import Path

    _, destination, state_manifest, desired_manifest = _legacy_cleanup_fields(
        cleanup_plan
    )
    reconcile_skill_roots(
        Path(destination),
        Path(state_manifest),
        desired_manifest,
    )


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    plugin_executor: Optional[Callable[[PluginOperation], Iterable[str]]] = None,
    legacy_cleaner: Optional[Callable[[object], None]] = None,
) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv[:1] == ["reconcile-plugins"]:
        args = _parse_reconcile_plugins_args(raw_argv[1:])
        try:
            reconcile_plugins(
                args.dest_dir,
                args.ownership_file,
                parse_plugin_plan(sys.stdin.read()),
                plugin_executor or _execute_plugin_command,
                legacy_cleaner or _cleanup_legacy_skill_roots,
            )
        except (FilterError, OSError, UnicodeError) as error:
            print(f"skill-filter: {error}", file=sys.stderr)
            return 1
        return 0
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
