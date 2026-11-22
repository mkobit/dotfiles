import pytest


@pytest.mark.integration
def test_gnupg_directory_is_private(host, chezmoi_dest):
    directory = host.file(str(chezmoi_dest / ".gnupg"))
    assert directory.is_directory
    assert directory.mode == 0o700
