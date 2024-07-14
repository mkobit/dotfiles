import src.dotfiles.git.config as c


def test_pull():
    pull = c.Pull(ff="only", rebase="interactive")

    assert pull.header() == "[pull]"
    file_options = pull.file_options()
    assert file_options.get("ff") == "only"
    assert file_options.get("rebase") == "interactive"
