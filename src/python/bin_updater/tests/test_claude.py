import json
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, override

import pytest

from bin_updater.catalog import discover_catalogs, load_catalog
from bin_updater.service import run_updates, update_tool
from tests.test_service import FakeClient

CATALOG = """[bin.claude]
version = "1.0.0"
minimum_release_age = "7d"
[bin.claude.updater]
source = "claude"
repo = "anthropics/claude-code"
manifest_url_format = "https://example.com/{version}/manifest.json"
# Native release URL stays unchanged.
[bin.claude.direct_release]
url_format = "https://example.com/{version}/{target}/claude"
[bin.claude.direct_release.platforms]
darwin_arm64 = "darwin-arm64"
darwin_amd64 = "darwin-x64"
linux_arm64 = "linux-arm64"
linux_amd64 = "linux-x64"
[bin.claude.direct_release.checksums]
darwin_arm64 = "old"
darwin_amd64 = "old"
linux_arm64 = "old"
linux_amd64 = "old"
"""


def manifest() -> dict[str, Any]:
    return {
        "version": "2.0.0",
        "platforms": {
            target: {"binary": "claude", "checksum": "A" * 64}
            for target in ("darwin-arm64", "darwin-x64", "linux-arm64", "linux-x64")
        },
    }


def test_claude_discovery_requires_opt_in(tmp_path: Path) -> None:
    path = tmp_path / "claude.toml"
    path.write_text(CATALOG)
    assert discover_catalogs(tmp_path)[0].repo == "anthropics/claude-code"
    path.write_text(CATALOG.replace('source = "claude"', 'source = "unsupported"'))
    assert not discover_catalogs(tmp_path)
    path.write_text(CATALOG.replace("[bin.claude.updater]", "[bin.claude.disabled]"))
    assert not discover_catalogs(tmp_path)


def test_claude_updates_all_platforms_and_keeps_notes(tmp_path: Path) -> None:
    path = tmp_path / "claude.toml"
    path.write_text(CATALOG)
    result = update_tool(
        load_catalog(path),
        FakeClient(
            [{"tag_name": "v2.0.0", "published_at": "2020-01-01T00:00:00Z", "body": "Release notes"}],
            {"https://example.com/2.0.0/manifest.json": json.dumps(manifest())},
        ),
    )
    updated = tomllib.loads(path.read_text())["bin"]["claude"]
    original = tomllib.loads(CATALOG)["bin"]["claude"]
    assert updated["version"] == "2.0.0"
    assert updated["direct_release"]["checksums"] == dict.fromkeys(original["direct_release"]["platforms"], "a" * 64)
    assert updated["direct_release"]["url_format"] == original["direct_release"]["url_format"]
    assert "# Native release URL stays unchanged." in path.read_text()
    assert "Release notes" in result.pr_body
    assert "anthropics/claude-code/compare/v1.0.0...v2.0.0" in result.pr_body


@pytest.mark.parametrize("failure", ["missing", "version", "checksum", "binary", "json", "http", "empty", "root"])
def test_claude_manifest_errors_leave_catalog_unchanged(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "claude.toml"
    original = CATALOG
    data = manifest()
    if failure == "missing":
        del data["platforms"]["linux-x64"]
    elif failure == "version":
        data["version"] = "3.0.0"
    elif failure == "checksum":
        data["platforms"]["linux-x64"]["checksum"] = "x" * 64
    elif failure == "binary":
        data["platforms"]["linux-x64"]["binary"] = "other"
    elif failure == "empty":
        start = original.index("[bin.claude.direct_release.platforms]")
        end = original.index("[bin.claude.direct_release.checksums]")
        original = original[:start] + "[bin.claude.direct_release.platforms]\n" + original[end:]
    path.write_text(original)

    class Client(FakeClient):
        @override
        def fetch_text(self, url: str) -> str:
            if failure == "http":
                raise RuntimeError("HTTP 404")
            if failure == "json":
                return "{invalid"
            return json.dumps([] if failure == "root" else data)

    try:
        result = run_updates(
            [load_catalog(path)], Client([{"tag_name": "v2.0.0", "published_at": "2020-01-01T00:00:00Z"}])
        )[0]
        assert result.error is not None
    except ValueError:
        assert failure == "empty"
    assert path.read_text() == original


def test_claude_uses_github_release_age(tmp_path: Path) -> None:
    path = tmp_path / "claude.toml"
    path.write_text(CATALOG)
    result = update_tool(
        load_catalog(path),
        FakeClient(
            [
                {"tag_name": "v3.0.0", "published_at": (datetime.now(UTC) - timedelta(days=1)).isoformat()},
                {"tag_name": "v2.0.0", "published_at": "2020-01-01T00:00:00Z"},
            ],
            {"https://example.com/2.0.0/manifest.json": json.dumps(manifest())},
        ),
        dry_run=True,
    )
    assert result.new_version == "2.0.0"
    assert path.read_text() == CATALOG
