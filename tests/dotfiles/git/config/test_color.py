import src.dotfiles.git.config as c


def test_color():
    color = c.Color(branch=True, status="always", ui=False)

    assert color.header() == '[color]'
    file_options = color.file_options()
    assert file_options.get('branch') == "true"
    assert file_options.get('status') == "always"
    assert file_options.get('ui') == "false"
