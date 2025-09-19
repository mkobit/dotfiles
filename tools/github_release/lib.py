import asyncio
import hashlib
import re
from typing import Any, Dict, List, Optional

import aiohttp


def select_asset(assets: List[Dict[str, Any]], asset_glob: str) -> Optional[Dict[str, Any]]:
    """Selects the best asset based on a glob pattern."""
    for asset in assets:
        if re.match(asset_glob, asset["name"]):
            return asset
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


def generate_toml_dict(version: str, sha256: str, url: str, asset_name: str) -> Dict[str, Any]:
    """Generates the chezmoi data structure as a dictionary."""
    return {
        "version": version,
        "url": url,
        "asset_name": asset_name,
        "sha256": sha256,
    }
