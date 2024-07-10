import pytest
import src.dotfiles.git.config as c

@pytest.mark.skip(reason="Not implemented yet")
def test_remote():
    stash = c.Remote()

    assert stash.header() == '[remote]'
    file_options = stash.file_options() # noqa: F841
    pytest.fail()
