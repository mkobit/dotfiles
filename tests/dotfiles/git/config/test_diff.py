import src.dotfiles.git.config as c


def test_diff():
    diff = c.Diff(
        algorithm="histogram",
        renames=True,
        compaction_heuristic=True,
        indent_heuristic=True,
    )

    assert diff.header() == "[diff]"
    file_options = diff.file_options()
    assert file_options.get("algorithm") == "histogram"
    assert file_options.get("renames") == "true"
    assert file_options.get("compactionHeuristic") == "true"
    assert file_options.get("indentHeuristic") == "true"
