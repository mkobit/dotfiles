def _test32_impl(ctx):
    ctx.download(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = "tmux.gz",
        executable = True
    )
    # The prompt explicitly says:
    # "can we replace the gzip execute with more bazel or starlark native command that isnt dependent on the system gzip command? also, with chmod"
    pass
