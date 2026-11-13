import functools
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bin_updater.cooldown import is_release_mature


class ReleaseInfo(BaseModel):
    tag_name: str
    published_at: str
    prerelease: bool = False
    assets: Sequence[Mapping[str, Any]] = Field(default_factory=tuple)


def extract_version_from_tag(tag: str, tag_format: str) -> str:
    """Extract semantic version string from git tag using expected tag format."""
    pattern = "^" + re.escape(tag_format).replace(r"\{version\}", r"(?P<version>[a-zA-Z0-9\.\-\+_]+)") + "$"
    match = re.match(pattern, tag)
    if match:
        return match.group("version")
    if tag_format == "{version}":
        return tag
    return tag.removeprefix("v")


def resolve_release_filename(tool_name: str, gr: Mapping[str, Any], version: str, platform: str) -> str:
    """Resolve release asset filename for specified platform."""
    platforms = gr.get("platforms")
    target = platforms.get(platform, "") if isinstance(platforms, Mapping) else ""
    os_name, _, arch_name = platform.partition("_")
    exts = gr.get("ext")
    ext = exts.get(platform, "") if isinstance(exts, Mapping) else ""
    filename_format = str(gr.get("filename_format", ""))
    replacements = {
        "{version}": version,
        "{target}": str(target),
        "{ext}": str(ext),
        "{os}": os_name,
        "{arch}": arch_name,
        "{tool}": tool_name,
        "{name}": tool_name,
    }
    return functools.reduce(lambda acc, item: acc.replace(item[0], item[1]), replacements.items(), filename_format)


def select_mature_release(
    releases: Sequence[Mapping[str, Any]],
    cooldown_seconds: int,
    include_prereleases: bool = False,
    now: datetime | None = None,
) -> Mapping[str, Any] | None:
    """Select the first release that meets stability and cooldown criteria."""

    def _is_mature(release: Mapping[str, Any]) -> bool:
        if not include_prereleases and release.get("prerelease", False):
            return False
        published_at = release.get("published_at")
        if not isinstance(published_at, str) or not published_at:
            return False
        try:
            return is_release_mature(published_at, cooldown_seconds, now=now)
        except ValueError:
            return False

    return next((r for r in releases if _is_mature(r)), None)
