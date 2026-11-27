from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
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
    new_sha = "a" * 64
    client = FakeClient(
        releases=[release],
        manifests={"https://example.com/manifest": f"{new_sha}  app-v2.0.0-linux-amd64.tar.gz\n"},
    )
    res = update_tool(cat, client, dry_run=False)
    assert res.changed is True
    assert res.new_version == "2.0.0"
    assert f'linux_amd64 = "{new_sha}"' in f.read_text(encoding="utf-8")


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


def test_update_tool_invalid_version_does_not_overwrite(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)
    client = FakeClient(releases=[{"tag_name": "nightly-build", "published_at": "2020-01-01T00:00:00Z"}])
    res = update_tool(cat, client)
    assert res.changed is False
    assert res.new_version == "1.0.0"
    assert f.read_text(encoding="utf-8") == TOML_TEMPLATE


def test_update_tool_dry_run_preserves_disk(tmp_path: Path) -> None:
    f = tmp_path / "app.toml"
    f.write_text(TOML_TEMPLATE, encoding="utf-8")
    cat = load_catalog(f)
    new_sha = "b" * 64
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
        manifests={"https://example.com/manifest": f"{new_sha}  app-v2.0.0-linux-amd64.tar.gz\n"},
    )
    res = update_tool(cat, client, dry_run=True)
    assert res.changed is True
    assert res.new_version == "2.0.0"
    assert f.read_text(encoding="utf-8") == TOML_TEMPLATE


def test_report_contains_all_stable_notes_in_version_order(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE.replace('tag_format = "v{version}"', 'tag_format = "app-v{version}"'))
    cat = load_catalog(path)
    releases = [
        {"tag_name": "v9.0.0", "published_at": "2020-01-01T00:00:00Z"},
        {
            "tag_name": "app-v2.0.0",
            "published_at": "2020-01-01T00:00:00Z",
            "body": "Last notes",
            "assets": [{"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"}],
        },
        {"tag_name": "app-v1.8.0", "body": "  "},
        {"tag_name": "app-v1.5.0", "body": "Middle notes", "html_url": "https://example.com/middle"},
        {"tag_name": "app-v1.6.0rc1", "body": "Pre-release"},
        {"tag_name": "app-v1.7.0", "draft": True, "body": "Draft"},
        {"tag_name": "app-v1.9.0", "prerelease": True, "body": "Preview"},
        {"tag_name": "app-v1.0.0", "body": "Old notes"},
    ]
    result = update_tool(cat, FakeClient(releases))
    assert result.pr_title == "chore(deps): bump app from 1.0.0 to 2.0.0"
    assert "| `1.0.0` | `2.0.0` | 2020-01-01 | `7d` |" in result.pr_body
    assert (
        result.pr_body.index("Middle notes")
        < result.pr_body.index("No release notes")
        < result.pr_body.index("Last notes")
    )
    assert "https://example.com/middle" in result.pr_body
    assert "https://github.com/org/app/releases/tag/app-v2.0.0" in result.pr_body
    assert "https://github.com/org/app/compare/app-v1.0.0...app-v2.0.0" in result.pr_body
    for included in ("Pre-release", "Preview"):
        assert included in result.pr_body
    for excluded in ("Draft", "Old notes", "v9.0.0"):
        assert excluded not in result.pr_body


def test_missing_second_platform_leaves_catalog_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    original = TOML_TEMPLATE.replace(
        'linux_amd64 = "linux-amd64"', 'linux_amd64 = "linux-amd64"\ndarwin_arm64 = "darwin-arm64"'
    )
    path.write_text(original)
    releases = [
        {
            "tag_name": "v2.0.0",
            "published_at": "2020-01-01T00:00:00Z",
            "assets": [{"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"}],
        }
    ]
    result = run_updates([load_catalog(path)], FakeClient(releases))[0]
    assert result.error is not None
    assert "darwin_arm64" in result.error
    assert path.read_text() == original


def test_api_failure_leaves_catalog_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE)

    class FailingClient(FakeClient):
        @override
        def list_releases(self, repo: str) -> Sequence[Mapping[str, Any]]:
            raise RuntimeError("API failure after page three")

    result = run_updates([load_catalog(path)], FailingClient([]))[0]
    assert result.error == "API failure after page three"
    assert path.read_text() == TOML_TEMPLATE


def test_oversized_notes_are_handed_off_in_full(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE)
    release = {
        "tag_name": "v2.0.0",
        "published_at": "2020-01-01T00:00:00Z",
        "body": "x" * 65536 + "Final release note.",
        "assets": [{"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"}],
    }
    result = run_updates([load_catalog(path)], FakeClient([release]))[0]
    assert result.error is None
    assert result.new_version == "2.0.0"
    assert result.pr_body.endswith("x" * 65536 + "Final release note.\n")
    assert 'version = "2.0.0"' in path.read_text()


def test_prereleases_are_reported_but_not_selected(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE)
    releases = [
        {"tag_name": "v3.0.0", "prerelease": True, "published_at": "2020-01-01T00:00:00Z"},
        {"tag_name": "v4.0.0rc1", "published_at": "2020-01-01T00:00:00Z"},
        {
            "tag_name": "v2.0.0",
            "published_at": "2020-01-01T00:00:00Z",
            "assets": [{"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"}],
        },
        {"tag_name": "v1.5.0", "prerelease": True, "body": "Flagged preview"},
        {"tag_name": "v1.8.0rc1", "body": "Candidate notes"},
        {"tag_name": "v1.9.0", "draft": True, "body": "Draft notes"},
    ]
    result = update_tool(load_catalog(path), FakeClient(releases))
    assert result.new_version == "2.0.0"
    assert "Flagged preview" in result.pr_body
    assert "Candidate notes" in result.pr_body
    assert "Draft notes" not in result.pr_body


def _large_release(version: str, published_at: str = "2020-01-01T00:00:00Z") -> Mapping[str, Any]:
    return {
        "tag_name": f"v{version}",
        "published_at": published_at,
        "body": version + "x" * 33000,
        "assets": [{"name": f"app-v{version}-linux-amd64.tar.gz", "browser_download_url": "https://example.com/bin"}],
    }


def test_large_note_ranges_keep_the_latest_mature_release(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE)
    client = FakeClient([_large_release("3.0.0"), _large_release("2.0.0")])
    result = update_tool(load_catalog(path), client)
    assert result.new_version == "3.0.0"
    assert "2.0.0" + "x" * 33000 in result.pr_body
    assert "3.0.0" + "x" * 33000 in result.pr_body


def test_large_notes_do_not_bypass_release_age(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(TOML_TEMPLATE)
    client = FakeClient(
        [
            _large_release("3.0.0", (datetime.now(UTC) - timedelta(days=1)).isoformat()),
            _large_release("2.0.0"),
            _large_release("1.5.0"),
        ]
    )
    result = update_tool(load_catalog(path), client)
    assert result.new_version == "2.0.0"
    assert "1.5.0" + "x" * 33000 in result.pr_body
    assert "3.0.0" not in result.pr_body


def test_run_updates_processes_multiple_catalogs_in_order_with_error_isolation(tmp_path: Path) -> None:
    catalogs = []
    for name in ("alpha", "broken", "gamma"):
        path = tmp_path / f"{name}.toml"
        path.write_text(TOML_TEMPLATE.replace("app", name), encoding="utf-8")
        catalogs.append(load_catalog(path))

    class MultiRepoClient(FakeClient):
        @override
        def list_releases(self, repo: str) -> Sequence[Mapping[str, Any]]:
            if repo == "org/broken":
                raise RuntimeError("broken repo")
            name = repo.split("/")[1]
            return [
                {
                    "tag_name": "v2.0.0",
                    "published_at": "2020-01-01T00:00:00Z",
                    "assets": [
                        {
                            "name": f"{name}-v2.0.0-linux-amd64.tar.gz",
                            "browser_download_url": f"https://example.com/{name}",
                        }
                    ],
                }
            ]

        @override
        def compute_asset_hash(self, url: str) -> str:
            return ("a" if url.endswith("alpha") else "c") * 64

    results = run_updates(catalogs, MultiRepoClient([]))
    assert [r.tool_name for r in results] == ["alpha", "broken", "gamma"]
    assert results[0].changed is True
    assert results[0].new_version == "2.0.0"
    assert results[1].changed is False
    assert results[1].error == "broken repo"
    assert results[2].changed is True
    assert results[2].new_version == "2.0.0"
    assert 'linux_amd64 = "' + "a" * 64 + '"' in (tmp_path / "alpha.toml").read_text(encoding="utf-8")
    assert 'linux_amd64 = "' + "c" * 64 + '"' in (tmp_path / "gamma.toml").read_text(encoding="utf-8")


def test_update_tool_computes_multiple_platform_hashes(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text(
        TOML_TEMPLATE.replace(
            'linux_amd64 = "linux-amd64"', 'linux_amd64 = "linux-amd64"\ndarwin_arm64 = "darwin-arm64"'
        ).replace('linux_amd64 = "oldhash"', 'linux_amd64 = "oldhash"\ndarwin_arm64 = "oldhash2"'),
        encoding="utf-8",
    )
    release = {
        "tag_name": "v2.0.0",
        "published_at": "2020-01-01T00:00:00Z",
        "assets": [
            {"name": "app-v2.0.0-linux-amd64.tar.gz", "browser_download_url": "https://example.com/linux"},
            {"name": "app-v2.0.0-darwin-arm64.tar.gz", "browser_download_url": "https://example.com/darwin"},
        ],
    }
    client = FakeClient(
        [release],
        hashes={
            "https://example.com/linux": "1" * 64,
            "https://example.com/darwin": "2" * 64,
        },
    )
    result = update_tool(load_catalog(path), client)
    assert result.changed is True
    updated = path.read_text(encoding="utf-8")
    assert f'linux_amd64 = "{"1" * 64}"' in updated
    assert f'darwin_arm64 = "{"2" * 64}"' in updated
