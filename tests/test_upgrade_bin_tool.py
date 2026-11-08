from pathlib import Path
from unittest.mock import patch

from scripts.upgrade_bin_tool import (
    extract_version_from_tag,
    find_latest_release,
    get_platform_checksums,
    parse_checksums_file,
    resolve_release_filename,
    update_toml_content,
    upgrade_tool,
)


def test_extract_version_from_tag():
    assert extract_version_from_tag("1.5.3", "{version}") == "1.5.3"
    assert extract_version_from_tag("v0.167.0", "v{version}") == "0.167.0"
    assert extract_version_from_tag("rust-v0.167.0", "rust-v{version}") == "0.167.0"
    assert extract_version_from_tag("v1.2.3", "v{version}") == "1.2.3"


def test_resolve_release_filename():
    gr_codex = {
        "filename_format": "codex-package-{target}.tar.gz",
        "platforms": {
            "darwin_arm64": "aarch64-apple-darwin",
            "linux_amd64": "x86_64-unknown-linux-musl",
        },
    }
    assert (
        resolve_release_filename("codex", gr_codex, "0.167.0", "darwin_arm64")
        == "codex-package-aarch64-apple-darwin.tar.gz"
    )
    assert (
        resolve_release_filename("codex", gr_codex, "0.167.0", "linux_amd64")
        == "codex-package-x86_64-unknown-linux-musl.tar.gz"
    )

    gr_fzf = {
        "filename_format": "fzf-{version}-{os}_{arch}.tar.gz",
        "platforms": {"linux_amd64": ""},
    }
    assert resolve_release_filename("fzf", gr_fzf, "0.74.5", "linux_amd64") == "fzf-0.74.5-linux_amd64.tar.gz"


def test_parse_checksums_file():
    content = """
    # Comments should be ignored
    af45ed45d940d7998809622c1c0296d3098ed7d7fad695284422c228bd454517  codex-package-aarch64-apple-darwin.tar.gz
    3d7c4c83296db63b5108e13612c77f3e5020b6c5f2fc004bee413a5cc92de899 *codex-package-x86_64-apple-darwin.tar.gz
    """
    checksums = parse_checksums_file(content)
    assert checksums["codex-package-aarch64-apple-darwin.tar.gz"] == (
        "af45ed45d940d7998809622c1c0296d3098ed7d7fad695284422c228bd454517"
    )
    assert checksums["codex-package-x86_64-apple-darwin.tar.gz"] == (
        "3d7c4c83296db63b5108e13612c77f3e5020b6c5f2fc004bee413a5cc92de899"
    )


def test_update_toml_content():
    raw_toml = """[bin.agy]
version = "1.5.3"

[bin.agy.github_releases]
repo = "google-antigravity/antigravity-cli"

[bin.agy.github_releases.checksums]
darwin_arm64 = "1111111111111111111111111111111111111111111111111111111111111111"
darwin_amd64 = "2222222222222222222222222222222222222222222222222222222222222222"
linux_amd64  = "3333333333333333333333333333333333333333333333333333333333333333"
linux_arm64  = "4444444444444444444444444444444444444444444444444444444444444444"
"""
    new_checksums = {
        "darwin_arm64": "aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111",
        "darwin_amd64": "bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222",
        "linux_amd64": "cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333",
        "linux_arm64": "dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444",
    }
    updated = update_toml_content(raw_toml, "1.6.0", new_checksums)
    assert 'version = "1.6.0"' in updated
    assert 'darwin_arm64 = "aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111"' in updated
    assert 'linux_arm64  = "dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444"' in updated


@patch("scripts.upgrade_bin_tool.fetch_json")
def test_find_latest_release(mock_fetch_json):
    mock_fetch_json.return_value = [
        {"tag_name": "v2.0.0-rc1", "prerelease": True},
        {"tag_name": "v1.9.0", "prerelease": False},
    ]
    rel = find_latest_release("test/repo")
    assert rel["tag_name"] == "v1.9.0"

    rel_pre = find_latest_release("test/repo", include_prereleases=True)
    assert rel_pre["tag_name"] == "v2.0.0-rc1"


@patch("scripts.upgrade_bin_tool.fetch_bytes")
def test_get_platform_checksums_with_checksum_file(mock_fetch_bytes):
    mock_fetch_bytes.return_value = (
        b"1234abcd  codex-package-aarch64-apple-darwin.tar.gz\n"
        b"5678ef01  codex-package-x86_64-unknown-linux-musl.tar.gz\n"
    )
    release = {
        "assets": [
            {
                "name": "codex-package_SHA256SUMS",
                "browser_download_url": "https://example.com/codex-package_SHA256SUMS",
            }
        ]
    }
    gr = {
        "filename_format": "codex-package-{target}.tar.gz",
        "platforms": {
            "darwin_arm64": "aarch64-apple-darwin",
            "linux_amd64": "x86_64-unknown-linux-musl",
        },
    }
    checksums = get_platform_checksums("codex", gr, "0.168.0", release)
    assert checksums["darwin_arm64"] == "1234abcd"
    assert checksums["linux_amd64"] == "5678ef01"


@patch("scripts.upgrade_bin_tool.compute_sha256_stream")
def test_get_platform_checksums_streaming(mock_compute):
    mock_compute.side_effect = ["hash_darwin_arm64", "hash_linux_amd64"]
    release = {
        "assets": [
            {
                "name": "agy_cli_mac_arm64.tar.gz",
                "browser_download_url": "https://example.com/mac_arm64",
            },
            {
                "name": "agy_cli_linux_x64.tar.gz",
                "browser_download_url": "https://example.com/linux_x64",
            },
        ]
    }
    gr = {
        "filename_format": "agy_cli_{target}.tar.gz",
        "platforms": {
            "darwin_arm64": "mac_arm64",
            "linux_amd64": "linux_x64",
        },
    }
    checksums = get_platform_checksums("agy", gr, "1.6.0", release)
    assert checksums["darwin_arm64"] == "hash_darwin_arm64"
    assert checksums["linux_amd64"] == "hash_linux_amd64"


def test_upgrade_tool_flow(tmp_path: Path):
    toml_file = tmp_path / "test_tool.toml"
    toml_file.write_text(
        """[bin.test_tool]
version = "1.0.0"

[bin.test_tool.github_releases]
repo = "example/test_tool"
filename_format = "test_tool-{target}.tar.gz"

[bin.test_tool.github_releases.platforms]
linux_amd64 = "x86_64-linux"

[bin.test_tool.github_releases.checksums]
linux_amd64 = "1111111111111111111111111111111111111111111111111111111111111111"
""",
        encoding="utf-8",
    )

    with (
        patch("scripts.upgrade_bin_tool.find_latest_release") as mock_rel,
        patch("scripts.upgrade_bin_tool.get_platform_checksums") as mock_sums,
    ):
        mock_rel.return_value = {
            "tag_name": "v1.1.0",
            "assets": [],
        }
        mock_sums.return_value = {"linux_amd64": "2222222222222222222222222222222222222222222222222222222222222222"}

        changed, old_v, new_v = upgrade_tool(toml_file, dry_run=False)
        assert changed is True
        assert old_v == "1.0.0"
        assert new_v == "1.1.0"

        updated = toml_file.read_text(encoding="utf-8")
        assert 'version = "1.1.0"' in updated
        assert 'linux_amd64 = "2222222222222222222222222222222222222222222222222222222222222222"' in updated
