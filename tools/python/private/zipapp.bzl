"""Bazel rules for creating Python zipapp executables with shebang.

This module provides rules to create standalone Python executables from py_binary targets.
The rule assumes --build_python_zip is enabled (either via command line or .bazelrc).
"""

def _python_zipapp_impl(ctx):
    """Creates an executable by prepending a shebang to a py_binary .zip file."""
    py_binary = ctx.attr.binary

    # Find the .zip file in the py_binary outputs
    zip_file = None
    for output in py_binary[DefaultInfo].files.to_list():
        if output.path.endswith(".zip"):
            zip_file = output
            break

    if not zip_file:
        fail("No .zip output found for {}. Enable --build_python_zip in .bazelrc".format(ctx.attr.binary.label))

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
            cfg = "target",
            doc = "py_binary target (built with --build_python_zip)",
        ),
    },
    executable = True,
    doc = """Creates a Python zipapp executable with shebang from a py_binary.

    Requires: --build_python_zip in .bazelrc

    Example:
        python_zipapp(
            name = "my_tool_exe",
            binary = ":my_tool",
        )
    """,
)
