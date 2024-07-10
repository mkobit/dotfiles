import src.dotfiles.git.config as c


def test_rebase():
    rebase = c.Rebase(stat=True, auto_stash=True, auto_squash=True)

    assert rebase.header() == '[rebase]'
    file_options = rebase.file_options()
    assert file_options.get('stat') == "true"
    assert file_options.get('autoStash') == "true"
    assert file_options.get('autoSquash') == "true"
