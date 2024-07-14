import src.dotfiles.git.config as c


def test_status():
    status = c.Status(
        ahead_behind=True,
        branch=True,
        relative_paths=True,
        short=True,
        submodule_summary=True,
        renames=True,
    )

    assert status.header() == "[status]"
    file_options = status.file_options()
    assert file_options.get("aheadBehind") == "true"
    assert file_options.get("branch") == "true"
    assert file_options.get("relativePaths") == "true"
    assert file_options.get("short") == "true"
    assert file_options.get("submoduleSummary") == "true"
    assert file_options.get("renames") == "true"
