"""
Linting aspects for the repository.
"""

load("@aspect_rules_lint//lint:ruff.bzl", "lint_ruff_aspect")
load("@rules_python//python:defs.bzl", "PyInfo")

# Define Ruff aspect
ruff = lint_ruff_aspect(
    binary = Label("//tools/lint:ruff_wrapper"),
    configs = [Label("//:pyproject.toml")],
)

# Define Mypy aspect (custom implementation)
def _mypy_aspect_impl(target, ctx):
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

    mypy_out = ctx.actions.declare_file(target.label.name + ".mypy.ok")
    py_info = target[PyInfo]

    mypy_args = ctx.actions.args()
    mypy_args.add("--config-file", ctx.file._config.path)
    mypy_args.add("--cache-dir", "/dev/null")
    mypy_args.add("--no-site-packages")

    for src in srcs:
        mypy_args.add(src.path)

    transitive_srcs = py_info.transitive_sources
    imports = py_info.imports.to_list()
    python_path = ":".join(["."] + imports)

    ctx.actions.run_shell(
        outputs = [mypy_out],
        inputs = depset(direct = srcs + [ctx.file._config], transitive = [transitive_srcs]),
        tools = [ctx.executable._mypy],
        command = """
        export PYTHONPATH={python_path}:$PYTHONPATH
        {mypy} $@ && touch {out}
        """.format(
            python_path = python_path,
            mypy = ctx.executable._mypy.path,
            out = mypy_out.path,
        ),
        arguments = [mypy_args],
        mnemonic = "MypyCheck",
        progress_message = "Type checking %s with Mypy" % target.label,
    )

    return [
        OutputGroupInfo(
            rules_python_lint = depset([mypy_out]),
        ),
    ]

mypy = aspect(
    implementation = _mypy_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_mypy": attr.label(
            default = Label("//tools/python:mypy"),
            executable = True,
            cfg = "exec",
        ),
        "_config": attr.label(
            default = Label("//:pyproject.toml"),
            allow_single_file = True,
        ),
    },
)
