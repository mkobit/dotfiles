# This file contains the known versions of tmux and their corresponding URLs and SHAs.

TMUX_VERSIONS = {
    "3.6": {
        "linux_amd64": {
            "urls": [
                "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-amd64.gz",
            ],
            "sha256": "380fa2387182ed4d922eb0f6b0deab059e8b5659b0c4d3c2baa9223e1b858e09",
            "strip_prefix": "",
            "is_archive": False,
        },
        "linux_arm64": {
            "urls": [
                "https://github.com/mjakob-gh/build-static-tmux/releases/download/v3.6/tmux.linux-arm64.gz",
            ],
            "sha256": "01a9df2d9921930365804d068d26b92063682855959bb3ee2d6b19346c385f6a",
            "strip_prefix": "",
            "is_archive": False,
        },
        "darwin_amd64": {
            "urls": [
                "https://ghcr.io/v2/homebrew/core/tmux/blobs/sha256:b0ca1f90384e487d2316bdcaef59ba4fdf63cb04fa561d424605f86935599563",
            ],
            "sha256": "b0ca1f90384e487d2316bdcaef59ba4fdf63cb04fa561d424605f86935599563",
            "strip_prefix": "tmux/3.6a/bin",
            "is_archive": True,
        },
        "darwin_arm64": {
            "urls": [
                "https://ghcr.io/v2/homebrew/core/tmux/blobs/sha256:9897a0d7b7e0159c1d09818d76e0ab88cc3fcdba8abd2bbbf349f84827ac87df",
            ],
            "sha256": "9897a0d7b7e0159c1d09818d76e0ab88cc3fcdba8abd2bbbf349f84827ac87df",
            "strip_prefix": "tmux/3.6a/bin",
            "is_archive": True,
        },
    },
}
