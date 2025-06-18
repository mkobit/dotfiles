"""
Mock toolchain for git when the real binary is not available.
"""

load(":toolchain.bzl", "GitInfo")

def _mock_git_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        gitinfo = GitInfo(
            git_path = ctx.attr.mock_path,
            git_version = "mock-version",
            env = ctx.attr.env,
            is_mock = True,
        ),
    )
    return [toolchain_info]

mock_git_toolchain = rule(
    implementation = _mock_git_toolchain_impl,
    attrs = {
        "mock_path": attr.string(
            doc = "Path to the mock git script",
            mandatory = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when invoking git",
            default = {},
        ),
    },
)
