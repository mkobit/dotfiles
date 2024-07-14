import src.dotfiles.git.config as c


def test_fetch():
    fetch = c.Fetch(
        mirror=True,
        prune=True,
        write_commit_graph=True,
        prune_tags=True,
        submodule="on-demand",
        tags="none",
    )

    assert fetch.header() == "[fetch]"
    file_options = fetch.file_options()
    assert file_options.get("mirror") == "true"
    assert file_options.get("prune") == "true"
    assert file_options.get("writeCommitGraph") == "true"
    assert file_options.get("pruneTags") == "true"
    assert file_options.get("submodule") == "on-demand"
    assert file_options.get("tags") == "none"
