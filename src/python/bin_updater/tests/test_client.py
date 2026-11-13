import hashlib

import httpx2
import pytest

from bin_updater.client import HttpxReleaseClient


def test_list_releases_success() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers["user-agent"] == "dotfiles-bin-updater/1.0"
        assert request.headers["authorization"] == "Bearer test-token"
        assert "repos/owner/repo/releases" in str(request.url)
        return httpx2.Response(200, json=[{"tag_name": "v1.0.0"}])

    mock_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = HttpxReleaseClient(token="test-token", client=mock_client)
    releases = client.list_releases("owner/repo")
    assert len(releases) == 1
    assert releases[0]["tag_name"] == "v1.0.0"


def test_list_releases_rate_limit() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(403, text="API rate limit exceeded")

    mock_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = HttpxReleaseClient(client=mock_client)
    with pytest.raises(RuntimeError, match="GitHub rate limit exceeded"):
        client.list_releases("owner/repo")


def test_fetch_text() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text="checksum-manifest-content")

    mock_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = HttpxReleaseClient(client=mock_client)
    assert client.fetch_text("https://example.com/manifest") == "checksum-manifest-content"


def test_compute_asset_hash() -> None:
    content = b"sample-binary-payload-data"
    expected_sha = hashlib.sha256(content).hexdigest()

    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=content)

    mock_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = HttpxReleaseClient(client=mock_client)
    assert client.compute_asset_hash("https://example.com/file.tar.gz") == expected_sha
