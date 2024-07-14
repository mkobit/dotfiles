import src.dotfiles.git.config as c


def test_commit():
    commit = c.Commit(gpg_sign=True, status=False, verbose=True)

    assert commit.header() == "[commit]"
    file_options = commit.file_options()
    assert file_options.get("gpgSign") == "true"
    assert file_options.get("status") == "false"
    assert file_options.get("verbose") == "true"
