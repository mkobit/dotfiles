import hashlib
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, Self

import httpx2

USER_AGENT = "dotfiles-bin-updater/1.0"


class ReleaseClient(Protocol):
    def list_releases(self, repo: str) -> Sequence[Mapping[str, Any]]: ...

    def fetch_text(self, url: str) -> str: ...

    def compute_asset_hash(self, url: str) -> str: ...


class HttpxReleaseClient:
    def __init__(self, token: str | None = None, client: httpx2.Client | None = None) -> None:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github.v3+json",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        self._headers = headers
        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx2.Client(timeout=30.0, headers=headers)
            self._owns_client = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def list_releases(self, repo: str, max_pages: int = 3) -> Sequence[Mapping[str, Any]]:
        per_page = 50
        releases: list[Mapping[str, Any]] = []
        for page in range(1, max_pages + 1):
            url = f"https://api.github.com/repos/{repo}/releases?per_page={per_page}&page={page}"
            resp = self._client.get(url, headers=self._headers, follow_redirects=True)
            if resp.status_code == 403:
                raise RuntimeError(f"GitHub rate limit exceeded or access forbidden for {repo}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                raise ValueError(f"Expected list of releases for {repo}, got {type(data).__name__}")
            releases.extend(data)
            if len(data) < per_page:
                break
        return releases

    def fetch_text(self, url: str) -> str:
        resp = self._client.get(url, headers=self._headers, follow_redirects=True)
        if resp.status_code == 403:
            raise RuntimeError(f"GitHub rate limit exceeded or access forbidden for {url}: {resp.text}")
        resp.raise_for_status()
        return resp.text

    def compute_asset_hash(self, url: str) -> str:
        hasher = hashlib.sha256()
        with self._client.stream("GET", url, headers=self._headers, follow_redirects=True, timeout=60.0) as resp:
            if resp.status_code == 403:
                raise RuntimeError(f"GitHub rate limit exceeded or access forbidden for {url}: {resp.text}")
            resp.raise_for_status()
            for chunk in resp.iter_bytes(chunk_size=65536):
                hasher.update(chunk)
        return hasher.hexdigest()
