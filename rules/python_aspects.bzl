"""
Python quality aspects for automatic ruff and mypy checking.

These aspects automatically apply to py_library, py_binary, and py_test targets,
providing consistent Python tooling without manual rule application.
"""

def _python_ruff_aspect_impl(target, ctx):
    """Aspect implementation for ruff format and lint checking."""

    # Only apply to Python rules
    if not ctx.rule.kind.startswith("py_"):
        return []

    # Get Python sources from the target
    sources = []
    if hasattr(ctx.rule.attr, "srcs") and ctx.rule.attr.srcs:
        for src in ctx.rule.attr.srcs:
            sources.extend([f for f in src.files.to_list() if f.extension == "py"])

    if not sources:
        return []

    # Python toolchain
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    outputs = []

    # Ruff format check
    format_output = ctx.actions.declare_file(target.label.name + "_ruff_format.out")
    ctx.actions.run_shell(
        inputs = sources,
        outputs = [format_output],
        tools = [python_exe],
        command = """{python} -m ruff format --check {files} > {output} 2>&1 || (echo "Ruff format failed for {target}:" && cat {output} && exit 1)""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in sources]),
            output = format_output.path,
            target = target.label,
        ),
        mnemonic = "RuffFormat",
        progress_message = "Checking format with ruff: %s" % target.label,
    )
    outputs.append(format_output)

    # Ruff lint check
    lint_output = ctx.actions.declare_file(target.label.name + "_ruff_lint.out")
    ctx.actions.run_shell(
        inputs = sources,
        outputs = [lint_output],
        tools = [python_exe],
        command = """{python} -m ruff check {files} > {output} 2>&1 || (echo "Ruff lint failed for {target}:" && cat {output} && exit 1)""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in sources]),
            output = lint_output.path,
            target = target.label,
        ),
        mnemonic = "RuffLint",
        progress_message = "Linting with ruff: %s" % target.label,
    )
    outputs.append(lint_output)

    return [
        OutputGroupInfo(
            ruff_format = depset([format_output]),
            ruff_lint = depset([lint_output]),
        ),
    ]

def _python_mypy_aspect_impl(target, ctx):
    """Aspect implementation for mypy type checking."""

    # Only apply to Python rules
    if not ctx.rule.kind.startswith("py_"):
        return []

    # Get Python sources from the target
    sources = []
    if hasattr(ctx.rule.attr, "srcs") and ctx.rule.attr.srcs:
        for src in ctx.rule.attr.srcs:
            sources.extend([f for f in src.files.to_list() if f.extension == "py"])

    if not sources:
        return []

    # Python toolchain
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    # Mypy type check
    mypy_output = ctx.actions.declare_file(target.label.name + "_mypy.out")
    ctx.actions.run_shell(
        inputs = sources,
        outputs = [mypy_output],
        tools = [python_exe],
        command = """{python} -m mypy --ignore-missing-imports {files} > {output} 2>&1 || (echo "Mypy failed for {target}:" && cat {output} && exit 1)""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in sources]),
            output = mypy_output.path,
            target = target.label,
        ),
        mnemonic = "Mypy",
        progress_message = "Type checking with mypy: %s" % target.label,
    )

    return [
        OutputGroupInfo(
            mypy = depset([mypy_output]),
        ),
    ]

# Define the aspects
python_ruff_aspect = aspect(
    implementation = _python_ruff_aspect_impl,
    attr_aspects = ["deps"],
    toolchains = ["@rules_python//python:toolchain_type"],
    doc = "Aspect for ruff format and lint checking on Python targets",
)

python_mypy_aspect = aspect(
    implementation = _python_mypy_aspect_impl,
    attr_aspects = ["deps"],
    toolchains = ["@rules_python//python:toolchain_type"],
    doc = "Aspect for mypy type checking on Python targets",
)

# Convenience rules to apply aspects
def _python_quality_test_impl(ctx):
    """Rule to run Python quality checks via aspects."""

    # This rule just triggers the aspects - the real work is in the aspects
    return [DefaultInfo()]

python_quality_test = rule(
    implementation = _python_quality_test_impl,
    attrs = {
        "targets": attr.label_list(
            aspects = [python_ruff_aspect, python_mypy_aspect],
            doc = "Python targets to check",
        ),
    },
    doc = "Rule to run ruff and mypy checks on Python targets via aspects",
)

# Macro for easy usage
def python_quality_suite(name, targets = None, **kwargs):
    """Macro to create Python quality test suite for targets.

    Args:
        name: Name of the test suite
        targets: List of Python targets to check. If None, checks all Python targets in package.
        **kwargs: Additional arguments passed to python_quality_test
    """
    if targets == None:
        # Auto-discover Python targets in the current package
        targets = native.existing_rules().keys()
        targets = [
            ":%s" % target
            for target in targets
            if target != name  # Don't include self
        ]

    python_quality_test(
        name = name,
        targets = targets,
        **kwargs
    )
