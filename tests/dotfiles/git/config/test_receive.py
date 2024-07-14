import src.dotfiles.git.config as c


def test_receive():
    receive = c.Receive(fsck_objects=True)

    assert receive.header() == "[receive]"
    file_options = receive.file_options()
    assert file_options.get("fsckObjects") == "true"
