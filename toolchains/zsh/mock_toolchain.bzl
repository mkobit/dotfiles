"""
Mock toolchain for zsh when the real binary is not available.
"""

load(":toolchain.bzl", "ZshInfo")

def _mock_zsh_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        zshinfo = ZshInfo(
            zsh_path = ctx.attr.mock_path,
            zsh_version = "mock-version",
            env = ctx.attr.env,
            is_mock = True,
        ),
    )
    return [toolchain_info]

mock_zsh_toolchain = rule(
    implementation = _mock_zsh_toolchain_impl,
    attrs = {
        "mock_path": attr.string(
            doc = "Path to the mock zsh script",
            mandatory = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when invoking zsh",
            default = {},
        ),
    },
)
