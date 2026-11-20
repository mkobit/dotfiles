import json
import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

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
    pr_title: str = ""
    pr_body: str = ""


def _release_version(release: Mapping[str, Any], tag_format: str) -> Version | None:
    if release.get("draft", False):
        return None
    tag = str(release.get("tag_name", ""))
    version = extract_version_from_tag(tag, tag_format)
    if "{version}" not in tag_format or tag_format.replace("{version}", version) != tag:
        return None
    try:
        parsed = Version(version)
    except InvalidVersion:
        return None
    return parsed


def _stable_version(release: Mapping[str, Any], tag_format: str) -> Version | None:
    parsed = _release_version(release, tag_format)
    if parsed is None or release.get("prerelease", False) or parsed.is_prerelease or parsed.is_devrelease:
        return None
    return parsed


def _release_notes(catalog: ToolCatalog, releases: Sequence[Mapping[str, Any]], target_version: str) -> str:
    old, new = Version(catalog.version), Version(target_version)
    selected = sorted(
        (
            (version, release)
            for release in releases
            if (version := _release_version(release, catalog.tag_format)) is not None and old < version <= new
        ),
        key=lambda item: item[0],
    )
    repo_url = f"https://github.com/{catalog.repo}"
    old_tag = quote(catalog.tag_format.replace("{version}", catalog.version), safe="")
    new_tag = quote(catalog.tag_format.replace("{version}", target_version), safe="")
    sections = [
        f"Update {catalog.name} from {catalog.version} to {target_version}.",
        f"[Compare changes]({repo_url}/compare/{old_tag}...{new_tag})",
    ]
    for _, release in selected:
        tag = str(release["tag_name"])
        url = release.get("html_url") or f"{repo_url}/releases/tag/{quote(tag, safe='')}"
        body = release.get("body")
        notes = body if isinstance(body, str) and body.strip() else "No release notes were provided."
        sections.append(f"## [{tag}]({url})\n\n{notes}")
    return "\n\n".join(sections) + "\n"


def _resolve_platform_checksums(
    catalog: ToolCatalog, target_version: str, release: Mapping[str, Any], client: ReleaseClient
) -> Mapping[str, str]:
    if catalog.source == "claude":
        return _claude_checksums(catalog, target_version, client)
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


def _claude_checksums(catalog: ToolCatalog, version: str, client: ReleaseClient) -> Mapping[str, str]:
    manifest = json.loads(client.fetch_text(catalog.manifest_url_format.format(version=version)))
    if not isinstance(manifest, Mapping) or manifest.get("version") != version:
        raise ValueError(f"Claude manifest version does not match {version}")
    platforms = manifest.get("platforms")
    if not isinstance(platforms, Mapping) or not catalog.platforms:
        raise ValueError("Claude manifest requires configured platforms")

    def checksum(target: str) -> str:
        item = platforms.get(target)
        if not isinstance(item, Mapping) or item.get("binary") != "claude":
            raise ValueError(f"Invalid Claude binary for platform {target}")
        value = item.get("checksum")
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
            raise ValueError(f"Invalid Claude checksum for platform {target}")
        return value.lower()

    return {platform: checksum(target) for platform, target in catalog.platforms.items()}


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
    stable_releases = [r for r in releases if _stable_version(r, catalog.tag_format) is not None]
    release = select_mature_release(stable_releases, cooldown)
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
        return ToolUpdateResult(
            tool_name=catalog.name, changed=False, old_version=catalog.version, new_version=catalog.version
        )
    pr_body = _release_notes(catalog, releases, target_version)
    new_checksums = _resolve_platform_checksums(catalog, target_version, release, client)
    if not dry_run:
        content = catalog.path.read_text(encoding="utf-8")
        updated = update_catalog_content(content, target_version, new_checksums)
        catalog.path.write_text(updated, encoding="utf-8")
    return ToolUpdateResult(
        tool_name=catalog.name,
        changed=True,
        old_version=catalog.version,
        new_version=target_version,
        pr_title=f"Update {catalog.name} from {catalog.version} to {target_version}",
        pr_body=pr_body,
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
