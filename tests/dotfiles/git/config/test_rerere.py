import src.dotfiles.git.config as c


def test_rerere():
    rerere = c.Rerere(auto_update=True, enabled=True)

    assert rerere.header() == "[rerere]"
    file_options = rerere.file_options()
    assert file_options.get("autoUpdate") == "true"
    assert file_options.get("enabled") == "true"
