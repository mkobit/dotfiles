import src.dotfiles.git.config as c


def test_push():
    push = c.Push(
        auto_setup_remote=True,
        default="upstream",
        follow_tags=True,
        gpg_sign="if-asked",
        recurse_submodules="only",
        use_force_if_includes=True,
        negotiate=True,
    )

    assert push.header() == "[push]"
    file_options = push.file_options()
    assert file_options.get("default") == "upstream"
    assert file_options.get("followTags") == "true"
    assert file_options.get("gpgSign") == "if-asked"
    assert file_options.get("recurseSubmodules") == "only"
    assert file_options.get("useForceIfIncludes") == "true"
    assert file_options.get("negotiate") == "true"
