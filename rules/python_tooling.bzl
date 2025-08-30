"""
Python tooling rules for ruff formatting, linting, and mypy type checking.

These rules use run_shell to invoke Python tools directly via the configured
Python toolchain and pip dependencies, with explicit outputs for tracking.
"""

def _python_ruff_format_test_impl(ctx):
    """Implementation for ruff format check test."""
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    output_file = ctx.actions.declare_file(ctx.label.name + ".out")

    ctx.actions.run_shell(
        inputs = ctx.files.srcs,
        outputs = [output_file],
        tools = [python_exe],
        command = """{python} -m ruff format --check {files} > {output} 2>&1 || (cat {output} && exit 1)""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in ctx.files.srcs]),
            output = output_file.path,
        ),
        mnemonic = "RuffFormatCheck",
        progress_message = "Checking Python formatting with ruff",
    )

    return [DefaultInfo(files = depset([output_file]))]

def _python_ruff_lint_test_impl(ctx):
    """Implementation for ruff lint check test."""
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    output_file = ctx.actions.declare_file(ctx.label.name + ".out")

    ctx.actions.run_shell(
        inputs = ctx.files.srcs,
        outputs = [output_file],
        tools = [python_exe],
        command = """{python} -m ruff check {files} > {output} 2>&1 || (cat {output} && exit 1)""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in ctx.files.srcs]),
            output = output_file.path,
        ),
        mnemonic = "RuffLintCheck",
        progress_message = "Checking Python linting with ruff",
    )

    return [DefaultInfo(files = depset([output_file]))]

def _python_mypy_test_impl(ctx):
    """Implementation for mypy type check test."""
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    output_file = ctx.actions.declare_file(ctx.label.name + ".out")

    # Use config file if provided
    config_arg = ""
    if ctx.file.config:
        config_arg = "--config-file {}".format(ctx.file.config.path)

    ctx.actions.run_shell(
        inputs = ctx.files.srcs + ([ctx.file.config] if ctx.file.config else []),
        outputs = [output_file],
        tools = [python_exe],
        command = """{python} -m mypy {config} {files} > {output} 2>&1 || (cat {output} && exit 1)""".format(
            python = python_exe.path,
            config = config_arg,
            files = " ".join([f.path for f in ctx.files.srcs]),
            output = output_file.path,
        ),
        mnemonic = "MypyTypeCheck",
        progress_message = "Type checking Python files with mypy",
    )

    return [DefaultInfo(files = depset([output_file]))]

def _python_ruff_format_impl(ctx):
    """Implementation for ruff format action."""
    python_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime
    python_exe = python_toolchain.interpreter

    output_file = ctx.actions.declare_file(ctx.label.name + ".out")

    ctx.actions.run_shell(
        inputs = ctx.files.srcs,
        outputs = [output_file],
        tools = [python_exe],
        command = """{python} -m ruff format {files} && echo "Formatted {count} files" > {output}""".format(
            python = python_exe.path,
            files = " ".join([f.path for f in ctx.files.srcs]),
            count = len(ctx.files.srcs),
            output = output_file.path,
        ),
        mnemonic = "RuffFormat",
        progress_message = "Formatting Python files with ruff",
    )

    return [DefaultInfo(files = depset([output_file]))]

# Rule definitions with minimal attributes
python_ruff_format_test = rule(
    implementation = _python_ruff_format_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to check formatting",
            allow_files = [".py"],
            mandatory = True,
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
    test = True,
)

python_ruff_lint_test = rule(
    implementation = _python_ruff_lint_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to lint",
            allow_files = [".py"],
            mandatory = True,
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
    test = True,
)

python_mypy_test = rule(
    implementation = _python_mypy_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to type check",
            allow_files = [".py"],
            mandatory = True,
        ),
        "config": attr.label(
            doc = "Optional mypy configuration file",
            allow_single_file = True,
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
    test = True,
)

python_ruff_format = rule(
    implementation = _python_ruff_format_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to format",
            allow_files = [".py"],
            mandatory = True,
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
    executable = True,
)
