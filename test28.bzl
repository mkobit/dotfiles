def _test28_impl(ctx):
    ctx.download(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = "tmux.gz",
    )
    # The extracted file has the name of the decompressed file, but permissions are `-rw-rw-r--`
    ctx.extract("tmux.gz", rename_files = {"tmux.linux-amd64": "tmux"})

    # Let's try to just write an executable shell script to wrap it since we can't chmod
    ctx.file("tmux_wrapper", "exec \"${BASH_SOURCE[0]%/*}/tmux\" \"$@\"\n", executable=True)
    res = ctx.execute(["ls", "-la"])
    print(res.stdout)
    ctx.file("BUILD.bazel", "")

test28 = repository_rule(implementation = _test28_impl)
