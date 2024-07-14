import src.dotfiles.git.config as c


def test_tag():
    tag = c.Tag(gpg_sign=True)

    assert tag.header() == "[tag]"
    file_options = tag.file_options()
    assert file_options.get("gpgSign") == "true"
