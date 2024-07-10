import src.dotfiles.git.config as c


def test_alias():
    alias = c.Alias(aliases={
        "cfg": "config --list",
        "cob": "checkout -b",
        "diff-changes": "diff --name-status -r",
        "wip": '''"!f() { git add . && git commit -m 'Work in progress'; }; f"''',
    })

    assert alias.header() == '[alias]'
    file_options = alias.file_options()
    assert file_options.get('cfg') == "config --list"
    assert file_options.get('cob') == "checkout -b"
    assert file_options.get('diff-changes') == "diff --name-status -r"
    assert file_options.get('wip') == '''"!f() { git add . && git commit -m 'Work in progress'; }; f"'''
