import src.dotfiles.git.config as c


def test_column():
    column = c.Column(ui="always")

    assert column.header() == '[column]'
    file_options = column.file_options()
    assert file_options.get('ui') == "always"
