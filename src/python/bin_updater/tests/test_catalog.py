from pathlib import Path

import pytest

from bin_updater.catalog import NonGitHubReleaseError, discover_catalogs, load_catalog, update_catalog_content

SAMPLE_TOML = """[bin.tool]
version = "1.0.0"

# Main releases
[bin.tool.github_releases]
repo = "owner/tool"
tag_format = "v{version}"
filename_format = "tool-v{version}-{target}.tar.gz"

[bin.tool.github_releases.platforms]
darwin_arm64 = "darwin-arm64"
linux_amd64 = "linux-amd64"

[bin.tool.github_releases.checksums]
darwin_arm64 = "111111"
linux_amd64 = "222222"
"""


def test_load_catalog(tmp_path: Path) -> None:
    catalog_file = tmp_path / "tool.toml"
    catalog_file.write_text(SAMPLE_TOML, encoding="utf-8")
    cat = load_catalog(catalog_file)
    assert cat.name == "tool"
    assert cat.version == "1.0.0"
    assert cat.repo == "owner/tool"
    assert cat.platforms["darwin_arm64"] == "darwin-arm64"


def test_load_catalog_missing_gr(tmp_path: Path) -> None:
    catalog_file = tmp_path / "other.toml"
    catalog_file.write_text('[bin.other]\nversion = "1.0.0"\n', encoding="utf-8")
    with pytest.raises(NonGitHubReleaseError, match=r"No \[bin.other.github_releases\]"):
        load_catalog(catalog_file)


def test_load_catalog_zero_cooldown(tmp_path: Path) -> None:
    catalog_file = tmp_path / "zero.toml"
    catalog_file.write_text(
        '[bin.zero]\nversion = "1.0.0"\nminimum_release_age = 0\n\n'
        '[bin.zero.github_releases]\nrepo = "owner/zero"\nminimum_release_age = "7d"\n'
        'filename_format = "zero-{version}"\n[bin.zero.github_releases.platforms]\nlinux_amd64 = "x"\n',
        encoding="utf-8",
    )
    cat = load_catalog(catalog_file)
    assert cat.minimum_release_age == 0


def test_discover_catalogs(tmp_path: Path) -> None:
    (tmp_path / "tool1.toml").write_text(SAMPLE_TOML, encoding="utf-8")
    (tmp_path / "nongh.toml").write_text('[bin.chafa]\nversion = "1.0.0"\n', encoding="utf-8")
    catalogs = discover_catalogs(tmp_path)
    assert len(catalogs) == 1
    assert catalogs[0].name == "tool"


def test_discover_catalogs_surfaces_schema_error(tmp_path: Path) -> None:
    (tmp_path / "broken.toml").write_text(
        '[bin.broken]\nversion = "1.0.0"\n[bin.broken.github_releases]\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="No repo specified"):
        discover_catalogs(tmp_path)


def test_update_catalog_content() -> None:
    updated = update_catalog_content(
        SAMPLE_TOML,
        new_version="2.0.0",
        new_checksums={"darwin_arm64": "aaaaaa", "linux_amd64": "bbbbbb"},
    )
    assert 'version = "2.0.0"' in updated
    assert 'darwin_arm64 = "aaaaaa"' in updated
    assert 'linux_amd64 = "bbbbbb"' in updated
    assert "# Main releases" in updated
