"""
Linting aspects for the repository.
"""

load("@aspect_rules_lint//lint:ruff.bzl", "lint_ruff_aspect")
load("@rules_python//python:defs.bzl", "PyInfo")

# Define Ruff aspect
ruff = lint_ruff_aspect(
    binary = "@@//tools/lint:ruff",
    configs = [Label("//:pyproject.toml")],
)

# Define Ty aspect (custom implementation)
def _ty_aspect_impl(target, ctx):
    if not (PyInfo in target):
        return []

    # Ignore external repositories and generated targets
    if target.label.workspace_root.startswith("external") or target.label.workspace_name != "":
        return []

    # Ignore requirements.test
    if "requirements.test" in target.label.name:
        return []

    srcs = []

    # Check for sources in the main repo
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.attr.srcs:
            if src.label.workspace_name == "":
                srcs += [f for f in src.files.to_list() if f.extension == "py" and f.is_source]

    if not srcs:
        return []

    ty_out = ctx.actions.declare_file(target.label.name + ".ty.ok")
    py_info = target[PyInfo]

    ty_args = ctx.actions.args()
    ty_args.add("check")

    for src in srcs:
        ty_args.add(src.path)

    transitive_srcs = py_info.transitive_sources
    imports = py_info.imports.to_list()
    python_path = ":".join(["."] + imports)

    ctx.actions.run_shell(
        outputs = [ty_out],
        inputs = depset(direct = srcs + [ctx.file._config], transitive = [transitive_srcs]),
        tools = [ctx.executable._ty],
        command = """
        export PYTHONPATH={python_path}:$PYTHONPATH
        {ty} $@ && touch {out}
        """.format(
            python_path = python_path,
            ty = ctx.executable._ty.path,
            out = ty_out.path,
        ),
        arguments = [ty_args],
        mnemonic = "TyCheck",
        progress_message = "Type checking %s with Ty" % target.label,
    )

    return [
        OutputGroupInfo(
            rules_python_lint = depset([ty_out]),
        ),
    ]

ty = aspect(
    implementation = _ty_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_ty": attr.label(
            default = Label("//tools/python:ty"),
            executable = True,
            cfg = "exec",
        ),
        "_config": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
)
