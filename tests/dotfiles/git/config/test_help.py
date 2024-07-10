from datetime import timedelta
import src.dotfiles.git.config as c


def test_help():
    help = c.Help(autocorrect=timedelta(seconds=5, milliseconds=500),format="man",all=True,verbose=True,version=True)

    assert help.header() == '[help]'
    file_options = help.file_options()
    assert file_options.get('autocorrect') == "5.5"
    assert file_options.get('format') == "man"
    assert file_options.get('all') == "true"
    assert file_options.get('verbose') == "true"
    assert file_options.get('version') == "true"
