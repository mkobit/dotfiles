def _test31_impl(ctx):
    ctx.download_and_extract(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = ".",
        rename_files = {"tmux.linux-amd64": "tmux"}
    )

    # Actually wait. Is there any way to change permissions in Starlark natively?
    # No native `chmod` except through `ctx.execute`. But `ctx.execute(["chmod", "+x", ...])` is just `chmod`.
    # Why is the user complaining about `chmod`? Because it's a "system execute command". But wait!
    # A shell command is also a system execute command.
    pass
