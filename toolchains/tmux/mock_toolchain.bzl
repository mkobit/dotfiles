"""
Mock toolchain rules for tmux when the binary is not available.
"""

load("//toolchains/tmux:toolchain.bzl", "TmuxInfo")

def _mock_tmux_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        tmuxinfo = TmuxInfo(
            tmux_path = ctx.attr.mock_path,
            tmux_version = "mock-version",
            env = {},
        ),
    )
    return [toolchain_info]

mock_tmux_toolchain = rule(
    implementation = _mock_tmux_toolchain_impl,
    attrs = {
        "mock_path": attr.string(
            doc = "Path to a mock tmux script",
            mandatory = True,
        ),
    },
)