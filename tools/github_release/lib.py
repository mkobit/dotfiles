import hashlib
import json
import re
import urllib.request
from typing import Any, Dict, List, Optional, TypedDict


class GitHubAsset(TypedDict):
    name: str
    browser_download_url: str


class ChezmoiExternal(TypedDict):
    type: str
    url: str
    sha256: str


def select_asset(assets: List[GitHubAsset], asset_glob: str) -> Optional[GitHubAsset]:
    """Selects the best asset based on a glob pattern."""
    for asset in assets:
        if re.match(asset_glob, asset["name"]):
            return asset
    return None


def get_release_info(repo: str, version: str) -> Dict[str, Any]:
    """Fetches release information from the GitHub API."""
    if version == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"

    with urllib.request.urlopen(url) as response:
        return json.load(response)


def get_asset_sha256(url: str) -> str:
    """Downloads an asset and returns its SHA256 checksum."""
    hasher = hashlib.sha256()
    with urllib.request.urlopen(url) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_chezmoi_external(url: str, sha256: str) -> ChezmoiExternal:
    """Generates the chezmoi external data structure."""
    return {
        "type": "archive",
        "url": url,
        "sha256": sha256,
    }