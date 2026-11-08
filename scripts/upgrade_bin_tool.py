#!/usr/bin/env python3
"""Upgrade binary tools managed in src/chezmoi/.chezmoidata/bin/*.toml.

Fetches GitHub releases, computes or extracts platform SHA256 checksums,
and updates the corresponding TOML file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

USER_AGENT = "dotfiles-upgrade-bin-tool/1.0"


def _validate_https_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs are allowed, got: {url}")


def fetch_json(url: str, token: str | None = None) -> Any:
    """Fetch JSON from a URL with optional GitHub Authorization header."""
    _validate_https_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url: str, token: str | None = None) -> bytes:
    """Fetch raw bytes from a URL."""
    _validate_https_url(url)
    headers = {"User-Agent": USER_AGENT}
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return resp.read()


def compute_sha256_stream(url: str, token: str | None = None) -> str:
    """Stream download a URL and compute its SHA256 hex digest."""
    _validate_https_url(url)
    headers = {"User-Agent": USER_AGENT}
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    hasher = hashlib.sha256()
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        while chunk := resp.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_latest_release(repo: str, token: str | None = None, include_prereleases: bool = False) -> dict[str, Any]:
    """Find the latest release for a repo, skipping prereleases unless requested."""
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    releases = fetch_json(url, token=token)
    if not isinstance(releases, list) or not releases:
        raise ValueError(f"No releases found for {repo}")

    for release in releases:
        if not include_prereleases and release.get("prerelease"):
            continue
        return release

    raise ValueError(f"No matching stable releases found for {repo}")


def extract_version_from_tag(tag: str, tag_format: str) -> str:
    """Extract version string from git tag using the tool's tag_format."""
    pattern = "^" + re.escape(tag_format).replace(r"\{version\}", r"(?P<version>[a-zA-Z0-9\.\-\+_]+)") + "$"
    match = re.match(pattern, tag)
    if match:
        return match.group("version")
    if tag_format == "{version}":
        return tag
    # Fallback: strip leading v if present
    return tag.removeprefix("v")


def resolve_release_filename(tool_name: str, gr: dict[str, Any], version: str, platform: str) -> str:
    """Resolve the release asset filename for a given platform."""
    target = gr.get("platforms", {}).get(platform, "")
    parts = platform.split("_", 1)
    os_name = parts[0]
    arch_name = parts[1] if len(parts) > 1 else ""
    ext = gr.get("ext", {}).get(platform, "")

    filename_fmt = gr.get("filename_format", "")
    return (
        filename_fmt.replace("{version}", version)
        .replace("{target}", target)
        .replace("{ext}", ext)
        .replace("{os}", os_name)
        .replace("{arch}", arch_name)
    )


def parse_checksums_file(content: str) -> dict[str, str]:
    """Parse a SHA256SUMS file into a mapping of filename -> sha256."""
    checksums: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            checksum = parts[0].strip()
            filename = parts[1].strip().lstrip("*")
            checksums[filename] = checksum
    return checksums


def get_platform_checksums(
    tool_name: str,
    gr: dict[str, Any],
    version: str,
    release: dict[str, Any],
    token: str | None = None,
) -> dict[str, str]:
    """Obtain sha256 checksums for each platform supported by the tool."""
    assets = release.get("assets", [])
    asset_by_name = {a.get("name"): a for a in assets}

    # Check if a release checksums file is published (e.g. codex-package_SHA256SUMS or SHA256SUMS)
    checksums_asset = None
    for name, asset in asset_by_name.items():
        if name and ("SHA256SUM" in name or name.endswith("_SHA256SUMS")):
            checksums_asset = asset
            break

    published_checksums: dict[str, str] = {}
    if checksums_asset:
        raw = fetch_bytes(checksums_asset["browser_download_url"], token=token)
        published_checksums = parse_checksums_file(raw.decode("utf-8", errors="replace"))

    results: dict[str, str] = {}
    platforms = gr.get("platforms", {})
    for platform in platforms:
        expected_filename = resolve_release_filename(tool_name, gr, version, platform)
        if expected_filename in published_checksums:
            results[platform] = published_checksums[expected_filename]
        elif expected_filename in asset_by_name:
            asset = asset_by_name[expected_filename]
            download_url = asset["browser_download_url"]
            results[platform] = compute_sha256_stream(download_url, token=token)
        else:
            raise ValueError(f"Asset '{expected_filename}' not found for platform '{platform}' in release {version}")

    return results


def update_toml_content(content: str, new_version: str, new_checksums: dict[str, str]) -> str:
    """Update version and platform checksums in the TOML string, preserving formatting."""
    # 1. Update version = "..."
    content = re.sub(
        r'(\bversion\s*=\s*")[^"]+(")',
        rf"\g<1>{new_version}\g<2>",
        content,
        count=1,
    )

    # 2. Update checksums under [.checksums] table
    for platform, sha in new_checksums.items():
        pattern = rf'({re.escape(platform)}\s*=\s*")[0-9a-fA-F]+(")'
        content = re.sub(pattern, rf"\g<1>{sha}\g<2>", content)

    return content


def upgrade_tool(
    toml_path: Path,
    dry_run: bool = False,
    token: str | None = None,
) -> tuple[bool, str, str]:
    """Upgrade a tool's TOML configuration.

    Returns: (changed, current_version, target_version)
    """
    raw_content = toml_path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_content)

    bin_table = data.get("bin", {})
    if not bin_table:
        raise ValueError(f"No [bin.<tool>] table found in {toml_path}")

    tool_name = next(iter(bin_table.keys()))
    tool_data = bin_table[tool_name]
    current_version = str(tool_data.get("version", ""))
    gr = tool_data.get("github_releases")
    if not gr:
        raise ValueError(f"Tool {tool_name} does not use github_releases in {toml_path}")

    repo = gr.get("repo")
    if not repo:
        raise ValueError(f"No repo specified in {toml_path}")

    tag_format = gr.get("tag_format", "v{version}")
    release = find_latest_release(repo, token=token)
    tag_name = release.get("tag_name", "")
    target_version = extract_version_from_tag(tag_name, tag_format)

    if current_version == target_version:
        return False, current_version, target_version

    new_checksums = get_platform_checksums(tool_name, gr, target_version, release, token=token)
    new_content = update_toml_content(raw_content, target_version, new_checksums)

    if not dry_run:
        toml_path.write_text(new_content, encoding="utf-8")

    return True, current_version, target_version


def main() -> int:
    parser = argparse.ArgumentParser(description="Upgrade chezmoi bin tool versions and checksums.")
    parser.add_argument("tool", help="Name of tool (e.g. agy, codex) or path to .toml")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying files")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for API calls (defaults to GITHUB_TOKEN env var)",
    )

    args = parser.parse_args()

    target_path = Path(args.tool)
    if not target_path.exists():
        # Treat as tool name under src/chezmoi/.chezmoidata/bin/<tool>.toml
        target_path = Path(f"src/chezmoi/.chezmoidata/bin/{args.tool}.toml")

    if not target_path.exists():
        print(f"Error: File '{target_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        changed, old_v, new_v = upgrade_tool(target_path, dry_run=args.dry_run, token=args.token)
        if changed:
            print(f"Upgraded {target_path.name}: {old_v} -> {new_v}")
        else:
            print(f"{target_path.name} is already up to date ({old_v})")
        return 0
    except Exception as e:
        print(f"Error upgrading {target_path}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
