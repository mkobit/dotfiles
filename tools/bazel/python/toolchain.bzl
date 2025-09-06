"""Bzl file for the ruff toolchain."""

load("@bazel_skylib//lib:platform_common.bzl", "platform_common")

RuffToolchainInfo = provider(
    fields = {
        "ruff": "The ruff executable.",
    },
)

PyrightToolchainInfo = provider(
    fields = {
        "pyright": "The pyright executable.",
    },
)

def _pyright_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        pyright_toolchain = PyrightToolchainInfo(
            pyright = ctx.executable.pyright,
        ),
    )
    return [toolchain_info]

pyright_toolchain = rule(
    implementation = _pyright_toolchain_impl,
    attrs = {
        "pyright": attr.label(
            executable = True,
            cfg = "exec",
            allow_files = True,
            default = Label("@pypi//pyright:pyright"),
        ),
    },
)

def _ruff_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        ruff_toolchain = RuffToolchainInfo(
            ruff = ctx.executable.ruff,
        ),
    )
    return [toolchain_info]

ruff_toolchain = rule(
    implementation = _ruff_toolchain_impl,
    attrs = {
        "ruff": attr.label(
            executable = True,
            cfg = "exec",
            allow_files = True,
            default = Label("@pypi//ruff:ruff"),
        ),
    },
)
