from datetime import UTC, datetime

from bin_updater.release import extract_version_from_tag, resolve_release_filename, select_mature_release


def test_extract_version_from_tag() -> None:
    assert extract_version_from_tag("v1.2.3", "v{version}") == "1.2.3"
    assert extract_version_from_tag("rust-v0.5.0", "rust-v{version}") == "0.5.0"
    assert extract_version_from_tag("2.9.0", "{version}") == "2.9.0"
    assert extract_version_from_tag("v3.4.1", "custom") == "3.4.1"


def test_resolve_release_filename() -> None:
    gr = {
        "platforms": {"darwin_arm64": "macOS_arm64", "linux_amd64": "linux_amd64"},
        "ext": {"darwin_arm64": "zip", "linux_amd64": "tar.gz"},
        "filename_format": "gh_{version}_{target}.{ext}",
    }
    assert resolve_release_filename("gh", gr, "2.97.0", "darwin_arm64") == "gh_2.97.0_macOS_arm64.zip"
    assert resolve_release_filename("gh", gr, "2.97.0", "linux_amd64") == "gh_2.97.0_linux_amd64.tar.gz"

    fzf_gr = {
        "platforms": {"darwin_arm64": "", "linux_amd64": ""},
        "filename_format": "fzf-{version}-{os}_{arch}.tar.gz",
    }
    assert resolve_release_filename("fzf", fzf_gr, "0.74.5", "darwin_arm64") == "fzf-0.74.5-darwin_arm64.tar.gz"


def test_select_mature_release() -> None:
    now = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    releases = [
        {"tag_name": "v2.0.0", "published_at": "2026-11-09T00:00:00Z", "prerelease": False},
        {"tag_name": "v1.9.0-rc1", "published_at": "2026-10-01T00:00:00Z", "prerelease": True},
        {"tag_name": "v1.8.0", "published_at": "2026-10-01T00:00:00Z", "prerelease": False},
    ]
    cooldown = 7 * 86400
    chosen = select_mature_release(releases, cooldown, include_prereleases=False, now=now)
    assert chosen is not None
    assert chosen["tag_name"] == "v1.8.0"

    with_pre = select_mature_release(releases, cooldown, include_prereleases=True, now=now)
    assert with_pre is not None
    assert with_pre["tag_name"] == "v1.9.0-rc1"
