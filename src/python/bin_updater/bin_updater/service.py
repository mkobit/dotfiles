from collections.abc import Mapping, Sequence
from typing import Any

from packaging.version import InvalidVersion, Version
from pydantic import BaseModel

from bin_updater.catalog import ToolCatalog, update_catalog_content
from bin_updater.checksums import find_checksum_manifest_asset, parse_checksum_manifest
from bin_updater.client import ReleaseClient
from bin_updater.cooldown import parse_cooldown_to_seconds
from bin_updater.release import extract_version_from_tag, resolve_release_filename, select_mature_release


class ToolUpdateResult(BaseModel):
    tool_name: str
    changed: bool
    old_version: str
    new_version: str
    error: str | None = None


def _resolve_platform_checksums(
    catalog: ToolCatalog, target_version: str, release: Mapping[str, Any], client: ReleaseClient
) -> Mapping[str, str]:
    assets = release.get("assets", ())
    asset_by_name = {str(a.get("name")): a for a in assets if isinstance(a, Mapping)}
    manifest_asset = find_checksum_manifest_asset(assets)
    url = manifest_asset.get("browser_download_url") if manifest_asset is not None else None
    published = parse_checksum_manifest(client.fetch_text(str(url))) if url is not None else {}

    def _hash_for_platform(platform: str) -> str:
        gr = {"platforms": catalog.platforms, "ext": catalog.ext, "filename_format": catalog.filename_format}
        expected = resolve_release_filename(catalog.name, gr, target_version, platform)
        if expected in published:
            return published[expected]
        asset = asset_by_name.get(expected)
        if asset is None or "browser_download_url" not in asset:
            raise ValueError(f"Asset '{expected}' not found for platform '{platform}' in release {target_version}")
        return client.compute_asset_hash(str(asset["browser_download_url"]))

    return {platform: _hash_for_platform(platform) for platform in catalog.platforms}


def update_tool(
    catalog: ToolCatalog,
    client: ReleaseClient,
    dry_run: bool = False,
    min_age_override: int | None = None,
) -> ToolUpdateResult:
    """Update a single tool catalog if a newer mature release is available."""
    min_age = min_age_override if min_age_override is not None else catalog.minimum_release_age
    cooldown = parse_cooldown_to_seconds(min_age)
    releases = client.list_releases(catalog.repo)
    release = select_mature_release(releases, cooldown)
    if release is None:
        return ToolUpdateResult(
            tool_name=catalog.name, changed=False, old_version=catalog.version, new_version=catalog.version
        )
    target_version = extract_version_from_tag(str(release.get("tag_name", "")), catalog.tag_format)
    if target_version == catalog.version:
        return ToolUpdateResult(
            tool_name=catalog.name, changed=False, old_version=catalog.version, new_version=catalog.version
        )
    try:
        if Version(target_version) <= Version(catalog.version):
            return ToolUpdateResult(
                tool_name=catalog.name, changed=False, old_version=catalog.version, new_version=catalog.version
            )
    except InvalidVersion:
        pass
    new_checksums = _resolve_platform_checksums(catalog, target_version, release, client)
    if not dry_run:
        content = catalog.path.read_text(encoding="utf-8")
        updated = update_catalog_content(content, target_version, new_checksums)
        catalog.path.write_text(updated, encoding="utf-8")
    return ToolUpdateResult(
        tool_name=catalog.name, changed=True, old_version=catalog.version, new_version=target_version
    )


def run_updates(
    catalogs: Sequence[ToolCatalog], client: ReleaseClient, dry_run: bool = False
) -> Sequence[ToolUpdateResult]:
    """Execute updates across catalogs isolating exceptions per tool."""

    def _safe_update(catalog: ToolCatalog) -> ToolUpdateResult:
        try:
            return update_tool(catalog, client, dry_run=dry_run)
        except Exception as exc:
            return ToolUpdateResult(
                tool_name=catalog.name,
                changed=False,
                old_version=catalog.version,
                new_version=catalog.version,
                error=str(exc),
            )

    return [_safe_update(c) for c in catalogs]
