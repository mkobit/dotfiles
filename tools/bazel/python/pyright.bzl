"""
A Bazel aspect that runs pyright on py_library and py_test targets.
"""

load("@rules_python//python:defs.bzl", "PyInfo")
load("//tools/bazel/python:toolchain.bzl", "PyrightToolchainInfo")

def _pyright_aspect_impl(target, ctx):
    """Implementation of the pyright aspect."""
    if PyInfo not in target:
        return []

    srcs = target[PyInfo].transitive_sources
    if not srcs.to_list():
        return []

    pyright_executable = ctx.toolchains["//tools/bazel/python:toolchain_type"].pyright_toolchain.pyright
    pyproject_toml = ctx.file._pyproject_toml

    output = ctx.actions.declare_file(ctx.label.name + ".pyright.out")

    args = ctx.actions.args()
    args.add("--outputjson")
    args.add("--project", pyproject_toml.path)

    ctx.actions.run(
        outputs = [output],
        inputs = depset(
            transitive = [srcs, depset([pyproject_toml, pyright_executable])],
        ),
        executable = pyright_executable,
        arguments = [args],
        mnemonic = "PyrightCheck",
        progress_message = "Running pyright on %{label}",
    )

    return [
        DefaultInfo(files = depset([output])),
    ]

pyright_aspect = aspect(
    implementation = _pyright_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_pyproject_toml": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
    toolchains = ["//tools/bazel/python:toolchain_type"],
)
