def _test27_impl(ctx):
    ctx.download(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = "tmux.gz",
    )
    # Does ctx.extract on a single .gz extract it to the output dir? Yes.
    ctx.extract("tmux.gz", rename_files = {"tmux.linux-amd64": "tmux"})

    # Check if executable?
    res = ctx.execute(["ls", "-la"])
    print(res.stdout)

test27 = repository_rule(implementation = _test27_impl)
