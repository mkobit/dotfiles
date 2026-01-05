"""Bazel rules for creating Python zipapp executables with shebang.

This module provides rules to create standalone Python executables from py_binary targets.
The rule assumes --build_python_zip is enabled (either via command line or .bazelrc).
"""

def _python_zipapp_impl(ctx):
    """Implementation for python_zipapp rule.

    This rule takes a py_binary that was built with --build_python_zip and
    creates an executable by prepending a Python shebang to the zip file.

    The py_binary must be built with --build_python_zip enabled. Add this to
    your .bazelrc to enable it by default:
        build --build_python_zip

    Or build with: bazel build --build_python_zip //target
    """
    py_binary = ctx.attr.binary

    # Find the .zip file in the py_binary outputs
    zip_file = None
    for output in py_binary[DefaultInfo].files.to_list():
        if output.path.endswith(".zip"):
            zip_file = output
            break

    if not zip_file:
        # If no .zip file found, the build might not have --build_python_zip enabled
        # Fall back to the main binary file and wrap it
        default_output = py_binary[DefaultInfo].files_to_run.executable
        if default_output:
            # This is not a zipapp, but we can still create a wrapper
            fail(
                "No .zip output found for {}. ".format(ctx.attr.binary.label) +
                "Ensure --build_python_zip is enabled.\n" +
                "Add to .bazelrc: build --build_python_zip\n" +
                "Or build with: bazel build --build_python_zip //target",
            )

    # Create output file with shebang prepended
    output = ctx.actions.declare_file(ctx.attr.name)

    ctx.actions.run_shell(
        inputs = [zip_file],
        outputs = [output],
        command = 'printf "#!/usr/bin/env python3\\n" > "{output}" && cat "{zip_file}" >> "{output}"'.format(
            output = output.path,
            zip_file = zip_file.path,
        ),
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
            doc = "The py_binary target to convert to a zipapp executable.",
        ),
    },
    executable = True,
    doc = """Creates a Python zipapp executable from a py_binary target.

This rule:
1. Takes a py_binary built with --build_python_zip
2. Prepends a Python shebang (#!/usr/bin/env python3)
3. Produces an executable file that can be run directly

IMPORTANT: The py_binary must be built with --build_python_zip enabled.
Add to .bazelrc to enable globally:
    build --build_python_zip

Example:
    python_zipapp(
        name = "my_tool_exe",
        binary = ":my_tool",
    )

Then build with:
    bazel build //path:my_tool_exe

And copy to ~/.local/bin/:
    cp bazel-bin/path/my_tool_exe ~/.local/bin/my_tool
""",
)
