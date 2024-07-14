import src.dotfiles.git.config as c


def test_pager():
    stash = c.Stash(show_include_untracked=True, show_patch=True, show_stat=True)

    assert stash.header() == "[stash]"
    file_options = stash.file_options()
    assert file_options.get("showIncludeUntracked") == "true"
    assert file_options.get("showPatch") == "true"
    assert file_options.get("showStat") == "true"
