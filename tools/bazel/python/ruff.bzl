"""
A Bazel aspect that runs ruff on py_library and py_test targets.
"""

load("@rules_python//python:defs.bzl", "PyInfo")
load("//tools/bazel/python:toolchain.bzl", "RuffToolchainInfo")

def _ruff_aspect_impl(target, ctx):
    """Implementation of the ruff aspect."""
    if PyInfo not in target:
        return []

    srcs = target[PyInfo].transitive_sources
    if not srcs.to_list():
        return []

    ruff_executable = ctx.toolchains["//tools/bazel/python:toolchain_type"].ruff_toolchain.ruff
    pyproject_toml = ctx.file._pyproject_toml

    output = ctx.actions.declare_file(ctx.label.name + ".ruff.out")

    args = ctx.actions.args()
    args.add("check")
    args.add("--config", pyproject_toml.path)
    args.add("--output-file", output.path)
    args.add(".")

    ctx.actions.run(
        outputs = [output],
        inputs = depset(
            transitive = [srcs, depset([pyproject_toml, ruff_executable])],
        ),
        executable = ruff_executable,
        arguments = [args],
        mnemonic = "RuffCheck",
        progress_message = "Running ruff on %{label}",
    )

    return [
        DefaultInfo(files = depset([output])),
    ]

ruff_aspect = aspect(
    implementation = _ruff_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_pyproject_toml": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
    toolchains = ["//tools/bazel/python:toolchain_type"],
)
