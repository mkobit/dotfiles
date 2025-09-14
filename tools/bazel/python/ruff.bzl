"""
A Bazel aspect that runs ruff on py_library and py_test targets.
"""

load("@rules_python//python:defs.bzl", "PyInfo")

def _ruff_aspect_impl(target, ctx):
    """Implementation of the ruff aspect."""
    if PyInfo not in target:
        return []

    srcs = target[PyInfo].transitive_sources
    src_files = srcs.to_list()
    if not src_files:
        return []

    ruff_executable = ctx.executable._ruff
    pyproject_toml = ctx.file._pyproject_toml

    # Create output file for ruff results
    output = ctx.actions.declare_file(target.label.name + ".ruff_output")

    args = ctx.actions.args()
    args.add("check")
    args.add("--config", pyproject_toml.path)

    # Add all source files explicitly instead of using "."
    args.add_all(src_files)

    ctx.actions.run(
        inputs = depset(
            direct = [pyproject_toml],
            transitive = [srcs],
        ),
        outputs = [output],
        executable = ruff_executable,
        arguments = [args],
        mnemonic = "RuffCheck",
        progress_message = "Running ruff on %{label}",
    )

    return []

ruff_aspect = aspect(
    implementation = _ruff_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_ruff": attr.label(
            default = Label("//tools/bazel/python:ruff"),
            executable = True,
            cfg = "exec",
        ),
        "_pyproject_toml": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
)
