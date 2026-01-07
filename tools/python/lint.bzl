"""
Aspect for running python linting and type checking using Ruff and Mypy.
"""

load("@rules_python//python:defs.bzl", "PyInfo")

def _python_lint_aspect_impl(target, ctx):
    # Only run on python rules
    if not (PyInfo in target):
        return []

    # Ignore external repositories
    if target.label.workspace_root.startswith("external"):
        return []

    # Ignore targets that are not in the main repository (e.g. implicit tests from rules_python)
    if target.label.workspace_name != "":
        return []

    # Ignore specific rules that are generated or external
    # This prevents linting external sources that might be aliased or wrapped
    if "requirements.test" in target.label.name:
        return []

    # We will pick up the sources from the target
    srcs = []
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.attr.srcs:
            # Check if it is a file (Artifact) before accessing is_source
            # Aspects see Targets, which can be Files (Artifacts) or Rules.
            # ctx.rule.attr.srcs is a list of Targets.
            # For a file target, we can check if it is a source artifact.

            # Bazel's Starlark API for aspect traversal on attributes yields Targets.
            # If the attribute is a list of labels (like srcs), we iterate over Targets.
            # However, for 'srcs', the targets are typically File targets.

            # Use checks to ensure we are dealing with a source file in the main repo

            # If src is a Rule (e.g. genrule producing .py), we might skip or handle differently.
            # If src is a File (InputFile or OutputFile), we check properties.

            # 'Target' object in Starlark: https://bazel.build/rules/lib/builtins/Target
            # It doesn't have is_source.

            # We need to look at the underlying files.
            # 'src' here is a Target. We can get files via src.files

            # But we want to filter by provenance (is it from this repo?)
            # The 'label' of the target tells us where it is defined.

            if src.label.workspace_name == "":
                srcs += [f for f in src.files.to_list() if f.extension == "py" and f.is_source]

    if not srcs:
        return []

    # Ruff linting
    ruff_out = ctx.actions.declare_file(target.label.name + ".ruff.ok")

    args = ctx.actions.args()
    args.add("check")
    args.add("--config", ctx.file._config.path)

    # Add sources
    for src in srcs:
        args.add(src.path)

    # Run ruff
    ctx.actions.run_shell(
        outputs = [ruff_out],
        inputs = srcs + [ctx.file._config],
        tools = [ctx.executable._ruff],
        command = "{ruff} $@ && touch {out}".format(
            ruff = ctx.executable._ruff.path,
            out = ruff_out.path,
        ),
        arguments = [args],
        mnemonic = "RuffLint",
        progress_message = "Linting %s with Ruff" % target.label,
    )

    # Mypy type checking
    # Technical Choice: We use Mypy over Pyright because:
    # 1. It is the reference implementation and industry standard.
    # 2. It integrates natively with Bazel's python rules (no Node.js requirement).
    # 3. It provides reliable, strict type checking compatible with our ecosystem.

    mypy_out = ctx.actions.declare_file(target.label.name + ".mypy.ok")

    # Get transitive sources and imports from PyInfo
    py_info = target[PyInfo]

    mypy_args = ctx.actions.args()
    mypy_args.add("--config-file", ctx.file._config.path)
    mypy_args.add("--cache-dir", "/dev/null")  # Disable cache for hermeticity
    mypy_args.add("--no-site-packages")

    # Add sources to check
    for src in srcs:
        mypy_args.add(src.path)

    # We need to include all transitive sources in the inputs
    transitive_srcs = py_info.transitive_sources
    imports = py_info.imports.to_list()

    # Construct PYTHONPATH
    # Include current directory (.) and all imports defined by dependencies
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
            rules_python_lint = depset([ruff_out, mypy_out]),
        ),
    ]

python_lint_aspect = aspect(
    implementation = _python_lint_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_ruff": attr.label(
            default = Label("//tools/python:ruff"),
            executable = True,
            cfg = "exec",
        ),
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
