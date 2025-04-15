"""
Rule for validating Vim configuration syntax.

This rule uses Vim's own parser to check for syntax errors in configuration files
by attempting to load them with the -u flag and checking the exit status.
"""

def _vim_validate_impl(ctx):
    """Implementation of vim_validate rule.
    
    Executes vim with the configuration file and captures any errors.
    The rule is both a test rule (when run with 'bazel test') and an
    executable that prints validation results (when run with 'bazel run').
    """
    input_file = ctx.file.config
    output_file = ctx.outputs.validation_result
    
    ctx.actions.run_shell(
        inputs = [input_file],
        outputs = [output_file],
        progress_message = "Validating vim configuration %s" % input_file.short_path,
        command = """
            if ! command -v vim &>/dev/null; then
                echo "VALIDATION SKIPPED: vim not installed" > "{output}"
                exit 0
            fi

            TMP_CONF=$(mktemp)
            cat "{input}" > "$TMP_CONF"

            if vim -u "$TMP_CONF" -c "quit" > /dev/null 2>&1; then
                echo "VALIDATION PASSED: vim configuration is valid" > "{output}"
            else
                echo "VALIDATION FAILED: vim configuration has errors" > "{output}"
                vim -u "$TMP_CONF" -c "quit" 2>&1 | head -10 >> "{output}"
                exit_code=1
            fi
            rm -f "$TMP_CONF"
            exit ${exit_code:-0}
        """.format(
            input = input_file.path,
            output = output_file.path,
        ),
    )
    
    # Create a runnable executable to display the validation result
    executable = ctx.actions.declare_file(ctx.label.name + ".sh")
    ctx.actions.write(
        output = executable,
        content = "cat \"{}\" && exit 0".format(output_file.short_path),
        is_executable = True,
    )
    
    return [
        DefaultInfo(
            files = depset([output_file]),
            executable = executable,
            runfiles = ctx.runfiles(files = [output_file]),
        ),
    ]

vim_validate = rule(
    implementation = _vim_validate_impl,
    attrs = {
        "config": attr.label(
            doc = "Vim configuration file to validate",
            allow_single_file = True,
            mandatory = True,
        ),
    },
    outputs = {
        "validation_result": "%{name}_validation.txt",
    },
    executable = True,
)