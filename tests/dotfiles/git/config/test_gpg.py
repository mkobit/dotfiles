import src.dotfiles.git.config as c


def test_gpg():
    gpg = c.Gpg(program="gpg2", sort_order="untrusted", use_agent=True)

    assert gpg.header() == '[gpg]'
    file_options = gpg.file_options()
    assert file_options.get('program') == "gpg2"
    assert file_options.get('sortOrder') == "untrusted"
    assert file_options.get('useAgent') == "true"
