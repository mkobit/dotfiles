from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, override

from bin_updater.catalog import load_catalog
from bin_updater.service import run_updates, update_tool

TOML_TEMPLATE = """[bin.app]
version = "1.0.0"

[bin.app.github_releases]
repo = "org/app"
tag_format = "v{version}"
filename_format = "app-v{version}-{target}.tar.gz"

[bin.app.github_releases.platforms]
linux_amd64 = "linux-amd64"

[bin.app.github_releases.checksums]
linux_amd64 = "oldhash"
"""


class FakeClient:
    def __init__(
        self,
        releases: Sequence[Mapping[str, Any]],
        manifests: Mapping[str, str] | None = None,
        hashes: Mapping[str, str] | None = None,
    ) -> None:
        self.releases = releases
        self.manifests = manifests or {}
        self.hashes = hashes or {}

    def list_releases(self, repo: str) -> Sequence[Mapping[str, Any]]:
        return self.releases

    def fetch_text(self, url: str) -> str:
        return self.manifests.get(url, "")

    def compute_asset_hash(self, url: str) -> str:
        return self.hashes.get(url, "computedhash")


def test_update_tool_already_current(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)
    client = FakeClient(releases=[{"tag_name": "v1.0.0", "published_at": "2020-01-01T00:00:00Z"}])
    res = update_tool(cat, client)
    assert res.changed is False
    assert res.new_version == "1.0.0"


def test_update_tool_with_manifest(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)
    release = {
        "tag_name": "v2.0.0",
        "published_at": "2020-01-01T00:00:00Z",
        "assets": [
            {"name": "app_SHA256SUMS", "browser_download_url": "https://example.com/manifest"},
            {"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"},
        ],
    }
    client = FakeClient(
        releases=[release],
        manifests={"https://example.com/manifest": "newhash  app-v2.0.0-linux-amd64.tar.gz\n"},
    )
    res = update_tool(cat, client, dry_run=False)
    assert res.changed is True
    assert res.new_version == "2.0.0"
    assert 'linux_amd64 = "newhash"' in f.read_text(encoding="utf-8")


def test_run_updates_error_isolation(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)

    class FailingClient(FakeClient):
        @override
        def list_releases(self, repo: str) -> Sequence[Mapping[str, Any]]:
            raise RuntimeError("API failure")

    results = run_updates([cat], FailingClient(releases=[]))
    assert len(results) == 1
    assert results[0].error == "API failure"
    assert results[0].changed is False


def test_update_tool_does_not_downgrade(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)
    client = FakeClient(releases=[{"tag_name": "v0.9.0", "published_at": "2020-01-01T00:00:00Z"}])
    res = update_tool(cat, client)
    assert res.changed is False
    assert res.new_version == "1.0.0"
