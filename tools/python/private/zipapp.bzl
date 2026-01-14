"""Bazel rules for creating Python zipapp executables with shebang.

This module provides rules to create standalone Python executables from py_binary targets.
It uses a configuration transition to ensure --build_python_zip is enabled for the
binary dependency, regardless of the global configuration.
"""

def _zip_transition_impl(settings, attr):
    return {"//command_line_option:build_python_zip": "true"}

_zip_transition = transition(
    implementation = _zip_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:build_python_zip"],
)

def _python_zipapp_impl(ctx):
    """Creates an executable by prepending a shebang to a py_binary .zip file."""
    # When an attribute has a transition, the value is a list of configured targets.
    # Since we have a 1:1 transition, we take the first element.
    py_binary = ctx.attr.binary[0]

    # Find the .zip file in the py_binary outputs
    zip_file = None
    for output in py_binary[DefaultInfo].files.to_list():
        if output.path.endswith(".zip"):
            zip_file = output
            break

    if not zip_file:
        fail("No .zip output found for {}. The transition should have enabled --build_python_zip.".format(ctx.attr.binary[0].label))

    # Create output file with shebang prepended
    output = ctx.actions.declare_file(ctx.attr.name)

    ctx.actions.run_shell(
        inputs = [zip_file],
        outputs = [output],
        command = 'printf "#!/usr/bin/env python3\\n" > "$1" && cat "$2" >> "$1"',
        arguments = [output.path, zip_file.path],
        mnemonic = "PythonZipapp",
        progress_message = "Creating zipapp executable %s" % ctx.label,
    )

    return [
        DefaultInfo(
            files = depset([output]),
            executable = output,
            runfiles = ctx.runfiles(files = [output]),
        ),
    ]

python_zipapp = rule(
    implementation = _python_zipapp_impl,
    attrs = {
        "binary": attr.label(
            mandatory = True,
            executable = True,
            cfg = _zip_transition,
            doc = "py_binary target (built with --build_python_zip)",
        ),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
    executable = True,
    doc = """Creates a Python zipapp executable with shebang from a py_binary.

    Automatically enables --build_python_zip for the binary dependency.

    Example:
        python_zipapp(
            name = "my_tool_exe",
            binary = ":my_tool",
        )
    """,
)
