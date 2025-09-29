import asyncio
import hashlib
import re
from typing import Any, Dict, List, Optional, TypedDict

import aiohttp


class GitHubAsset(TypedDict):
    name: str
    browser_download_url: str


class ChezmoiData(TypedDict):
    version: str
    checksums: Dict[str, str]


# A mapping of regex patterns to architecture/OS keys
ARCH_OS_PATTERNS = {
    "darwin_amd64": r".*darwin.*(x86_64|amd64).*",
    "darwin_arm64": r".*darwin.*(arm64|aarch64).*",
    "linux_amd64": r".*linux.*(x86_64|amd64).*",
    "linux_arm64": r".*linux.*(arm64|aarch64).*",
}


def extract_arch_os(asset_name: str) -> Optional[str]:
    """Extracts the architecture and OS from an asset name."""
    for key, pattern in ARCH_OS_PATTERNS.items():
        if re.match(pattern, asset_name, re.IGNORECASE):
            return key
    return None


async def get_release_info(session: aiohttp.ClientSession, repo: str, version: str) -> Dict[str, Any]:
    """Fetches release information from the GitHub API."""
    if version == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"

    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def get_asset_sha256(session: aiohttp.ClientSession, url: str) -> str:
    """Downloads an asset and returns its SHA256 checksum."""
    hasher = hashlib.sha256()
    async with session.get(url) as response:
        response.raise_for_status()
        while True:
            chunk = await response.content.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


async def get_checksums_from_file(session: aiohttp.ClientSession, url: str) -> Dict[str, str]:
    """Downloads and parses a checksum file."""
    checksums = {}
    async with session.get(url) as response:
        response.raise_for_status()
        text = await response.text()
        for line in text.splitlines():
            parts = line.split()
            if len(parts) == 2:
                sha, filename = parts
                filename = filename.lstrip("./")
                checksums[filename] = sha
    return checksums