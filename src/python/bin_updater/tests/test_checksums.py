from bin_updater.checksums import find_checksum_manifest_asset, parse_checksum_manifest


def test_parse_checksum_manifest() -> None:
    content = """
    # SHA256 checksums file
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  foo.tar.gz
    d41d8cd98f00b204e9800998ecf8427e  *bar.zip

    # Another comment
    da39a3ee5e6b4b0d3255bfef95601890afd80709 baz
    """
    manifest = parse_checksum_manifest(content)
    assert manifest["foo.tar.gz"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert manifest["bar.zip"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert manifest["baz"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


def test_find_checksum_manifest_asset() -> None:
    assets = [
        {"name": "foo-v1.0.tar.gz", "browser_download_url": "https://example.com/foo.tar.gz"},
        {"name": "SHA256SUMS.sig", "browser_download_url": "https://example.com/sig"},
        {"name": "tool_SHA256SUMS", "browser_download_url": "https://example.com/manifest"},
    ]
    manifest = find_checksum_manifest_asset(assets)
    assert manifest is not None
    assert manifest["name"] == "tool_SHA256SUMS"


def test_find_checksum_manifest_asset_none() -> None:
    assets = [
        {"name": "app-darwin.tar.gz"},
        {"name": "app-linux.tar.gz"},
    ]
    assert find_checksum_manifest_asset(assets) is None
