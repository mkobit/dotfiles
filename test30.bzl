def _test30_impl(ctx):
    ctx.download_and_extract(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = ".",
        rename_files = {"tmux.linux-amd64": "tmux"}
    )

    # Can we just use `os.chmod` in a python script?
    ctx.file("chmod.py", "import os, sys\nos.chmod(sys.argv[1], 0o755)")
    # But wait, bazel doesn't guarantee python on PATH or what is the Python interpreter?
    res = ctx.execute([ctx.which("python3") or ctx.which("python"), "chmod.py", "tmux"])
    print(res.stdout)
    res2 = ctx.execute(["ls", "-la"])
    print(res2.stdout)
    ctx.file("BUILD.bazel", "")

test30 = repository_rule(implementation = _test30_impl)
