"""
A Bazel aspect that runs pyright type checking on py_library and py_test targets.
"""

load("@rules_python//python:defs.bzl", "PyInfo")

def _pyright_aspect_impl(target, ctx):
    """Implementation of the pyright aspect."""
    if PyInfo not in target:
        return []

    srcs = target[PyInfo].transitive_sources
    src_files = srcs.to_list()
    if not src_files:
        return []

    pyright_executable = ctx.executable._pyright
    pyproject_toml = ctx.file._pyproject_toml

    # Create output file for pyright results
    output = ctx.actions.declare_file(target.label.name + ".pyright_output")

    args = ctx.actions.args()

    # Add pyright-specific arguments
    args.add("--project", pyproject_toml.dirname)

    # Add all source files explicitly
    args.add_all(src_files)

    ctx.actions.run(
        inputs = depset(
            direct = [pyproject_toml],
            transitive = [srcs],
        ),
        outputs = [output],
        executable = pyright_executable,
        arguments = [args],
        mnemonic = "PyrightCheck",
        progress_message = "Running pyright on %{label}",
    )

    return []

pyright_aspect = aspect(
    implementation = _pyright_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_pyright": attr.label(
            default = Label("//tools/bazel/python:pyright"),
            executable = True,
            cfg = "exec",
        ),
        "_pyproject_toml": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
)
