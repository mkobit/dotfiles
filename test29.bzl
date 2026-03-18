def _test29_impl(ctx):
    ctx.download(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = "tmux.gz",
    )
    # The prompt explicitly says:
    # "can we replace the gzip execute with more bazel or starlark native command that isnt dependent on the system gzip command? also, with chmod"

    # Actually wait. Is there any way to change permissions in Starlark natively?
    # `repository_ctx.download_and_extract` natively extracts gz! Wait, test15 failed. But `ctx.download_and_extract` extracts a gz file into a directory.
    # What if we use `ctx.download_and_extract` and then `ctx.execute(["chmod", "+x", ...])`? The prompt says "also, with chmod". Meaning, "replace gzip execute with ... and replace chmod execute with ...".

    # Is there a native `chmod` alternative? Wait, can we extract using python?
    pass
