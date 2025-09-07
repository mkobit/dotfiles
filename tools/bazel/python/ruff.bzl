"""
A Bazel aspect that runs ruff on py_library and py_test targets.
"""

load("@rules_python//python:defs.bzl", "PyInfo")

def _ruff_aspect_impl(target, ctx):
    """Implementation of the ruff aspect."""
    if PyInfo not in target:
        return []

    srcs = target[PyInfo].transitive_sources
    if not srcs.to_list():
        return []

    ruff_executable = ctx.executable._ruff
    pyproject_toml = ctx.file._pyproject_toml

    repo = ctx.label.workspace_name
    package_path = ctx.label.package.replace("/", "_")
    output_name = repo + "_" + package_path + "_" + ctx.label.name + ".ruff.out"
    output = ctx.actions.declare_file(output_name)
    ctx.actions.write(output, "Ruff aspect run.")

    args = ctx.actions.args()
    args.add("check")
    args.add("--config", pyproject_toml.path)
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
        "_ruff": attr.label(
            default = Label("//tools/bazel/python:ruff_runner"),
            executable = True,
            cfg = "exec",
        ),
        "_pyproject_toml": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
)
