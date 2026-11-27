import hashlib
from typing import Any

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


def test_client_does_not_mutate_caller_headers() -> None:
    mock_client = httpx2.Client(transport=httpx2.MockTransport(lambda _r: httpx2.Response(200, json=[])))
    original_headers = dict(mock_client.headers)
    with HttpxReleaseClient(token="secret", client=mock_client) as client:
        client.list_releases("owner/repo")
    assert dict(mock_client.headers) == original_headers


def test_client_context_manager_closes_owned_client() -> None:
    with HttpxReleaseClient() as client:
        assert not client._client.is_closed
    assert client._client.is_closed


def test_list_releases_reads_all_pages() -> None:
    pages = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        page = int(request.url.params["page"])
        per_page = int(request.url.params["per_page"])
        pages.append(page)
        assert per_page == 100
        return httpx2.Response(200, json=[{"tag_name": f"v{page}.0.0"}] * (per_page if page <= 4 else 1))

    client = HttpxReleaseClient(client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    assert len(client.list_releases("org/app")) == 401
    assert pages == [1, 2, 3, 4, 5]


def test_list_releases_late_api_error() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if int(request.url.params["page"]) == 4:
            return httpx2.Response(500)
        per_page = int(request.url.params["per_page"])
        return httpx2.Response(200, json=[{"tag_name": "v2.0.0"}] * per_page)

    client = HttpxReleaseClient(client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    with pytest.raises(httpx2.HTTPStatusError):
        client.list_releases("org/app")


def test_vendor_manifest_does_not_receive_github_token() -> None:
    seen = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request.url.host)
        if request.url.host == "api.github.com":
            assert request.headers["authorization"] == "Bearer secret"
            return httpx2.Response(200, json=[])
        assert "authorization" not in request.headers
        return httpx2.Response(200, text="manifest")

    with (
        httpx2.Client(transport=httpx2.MockTransport(handler)) as transport,
        HttpxReleaseClient(token="secret", client=transport) as client,
    ):
        client.list_releases("anthropics/claude-code")
        assert client.fetch_text("https://downloads.claude.ai/manifest.json") == "manifest"
    assert seen == ["api.github.com", "downloads.claude.ai"]


def test_owned_client_keeps_github_token_off_vendor_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    original_client = httpx2.Client
    seen = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request.url.host)
        if request.url.host == "api.github.com":
            assert request.headers["authorization"] == "Bearer secret"
            return httpx2.Response(200, json=[])
        assert "authorization" not in request.headers
        return httpx2.Response(200, text="manifest")

    def client_factory(**kwargs: Any) -> httpx2.Client:
        return original_client(**kwargs, transport=httpx2.MockTransport(handler))

    monkeypatch.setattr(httpx2, "Client", client_factory)
    with HttpxReleaseClient(token="secret") as client:
        client.list_releases("anthropics/claude-code")
        assert client.fetch_text("https://downloads.claude.ai/manifest.json") == "manifest"
    assert seen == ["api.github.com", "downloads.claude.ai"]
