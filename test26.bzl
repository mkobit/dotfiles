def _test26_impl(ctx):
    ctx.download(
        url = "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
        output = "tmux.gz",
    )
    # Does ctx.extract natively decompress raw gz file if given a different output?
    ctx.extract("tmux.gz") # We tested this, it failed with "Expected a file with a .zip ... suffix" wait no, download_and_extract failed for appimage.gz with "Input is not in the .gz format", but for actual .gz files it works. Wait, test3.bzl failed because it was a 404 URL.
    pass
