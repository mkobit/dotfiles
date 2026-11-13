from bin_updater.checksums import find_checksum_manifest_asset, parse_checksum_manifest


def test_parse_checksum_manifest() -> None:
    hash1 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    hash2 = "a" * 64
    content = f"""
    # SHA256 checksums file
    {hash1}  foo.tar.gz
    {hash2}  *./bar.zip

    # Invalid hashes should be rejected
    d41d8cd98f00b204e9800998ecf8427e  short-md5.tar.gz
    {"z" * 64}  nonhex.tar.gz
    """
    manifest = parse_checksum_manifest(content)
    assert manifest["foo.tar.gz"] == hash1
    assert manifest["bar.zip"] == hash2
    assert "short-md5.tar.gz" not in manifest
    assert "nonhex.tar.gz" not in manifest


def test_find_checksum_manifest_asset() -> None:
    assets = [
        {"name": "foo-v1.0.tar.gz", "browser_download_url": "https://example.com/foo.tar.gz"},
        {"name": "SHA256SUMS.sig", "browser_download_url": "https://example.com/sig"},
        {"name": "SHA256SUMS.minisig", "browser_download_url": "https://example.com/minisig"},
        {"name": "checksums.txt.sigstore", "browser_download_url": "https://example.com/sigstore"},
        {"name": "tool_SHA256SUMS", "browser_download_url": "https://example.com/manifest"},
    ]
    manifest = find_checksum_manifest_asset(assets)
    assert manifest is not None
    assert manifest["name"] == "tool_SHA256SUMS"


def test_find_checksum_manifest_asset_lowercase() -> None:
    assets = [
        {"name": "sha256sums.txt.minisig", "browser_download_url": "https://example.com/minisig"},
        {"name": "sha256sums.txt", "browser_download_url": "https://example.com/manifest"},
    ]
    manifest = find_checksum_manifest_asset(assets)
    assert manifest is not None
    assert manifest["name"] == "sha256sums.txt"


def test_find_checksum_manifest_asset_none() -> None:
    assets = [
        {"name": "app-darwin.tar.gz"},
        {"name": "app-linux.tar.gz"},
    ]
    assert find_checksum_manifest_asset(assets) is None
