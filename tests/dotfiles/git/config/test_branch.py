import src.dotfiles.git.config as c


def test_branch():
    branch = c.Branch(auto_set_up_rebase="always", sort="-committerdate")

    assert branch.header() == "[branch]"
    file_options = branch.file_options()
    assert file_options.get("autoSetUpRebase") == "always"
    assert file_options.get("sort") == "-committerdate"
