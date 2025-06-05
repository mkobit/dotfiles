"""
Implementation of Vim configuration rules.
"""

def _vim_config_impl(ctx):
    """Implementation of vim_config rule."""
    output = ctx.actions.declare_file(ctx.attr.name + ".vim")
    
    # Build a list of input files for the action
    input_files = []
    for src in ctx.attr.srcs:
        input_files.extend(src.files.to_list())
    
    # Generate the command to combine configuration files
    cmd = ["#!/bin/bash", "set -euo pipefail", ""]
    
    # Add header if specified
    header = ctx.attr.header
    if header:
        # Replace $(date) with actual date
        header = header.replace("$(date)", "$(date '+%Y-%m-%d %H:%M:%S')")
        cmd.append("echo '{}' > {}".format(header, output.path))
    else:
        cmd.append("touch {}".format(output.path))
    
    # Add a newline after the header
    cmd.append("echo '' >> {}".format(output.path))
    
    # Include each source file
    for i, src_file in enumerate(input_files):
        cmd.append("echo '\" {} configuration' >> {}".format(
            src_file.basename, output.path))
        cmd.append("cat {} >> {}".format(src_file.path, output.path))
        cmd.append("echo '' >> {}".format(output.path))
    
    # Add footer if specified
    if ctx.attr.footer:
        cmd.append("echo '{}' >> {}".format(ctx.attr.footer, output.path))
    
    # Join commands into a shell script
    cmd_str = "\n".join(cmd)
    
    # Execute the command to create the output file
    ctx.actions.run_shell(
        outputs = [output],
        inputs = input_files,
        command = cmd_str,
        mnemonic = "VimConfig",
        progress_message = "Generating Vim configuration %s" % output.path,
    )
    
    return [DefaultInfo(
        files = depset([output]),
        runfiles = ctx.runfiles(files = [output]),
    )]

vim_config = rule(
    implementation = _vim_config_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Input Vim configuration files to be combined",
            allow_files = [".vim"],
            mandatory = True,
        ),
        "header": attr.string(
            doc = "Optional header to include at the top of the generated config",
            default = "\" Generated Vim configuration",
        ),
        "footer": attr.string(
            doc = "Optional footer to include at the end of the generated config",
            default = "\" End of generated configuration",
        ),
    },
)

def _vim_test_impl(ctx):
    """Implementation of vim_test rule."""
    # Get the Vim configuration file to test
    config = ctx.file.config
    
    # Create a test script
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")
    
    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -euo pipefail

# Use the system vim or the one defined in PATH
VIM="${{VIM_BIN:-vim}}"

CONFIG="{config}"
echo "Testing Vim configuration: $CONFIG with vim executable: $VIM"

# Validate syntax
$VIM -u NONE -N --cmd "source $CONFIG" --cmd "quit" || {{
    echo "Vim configuration has syntax errors"
    exit 1
}}

echo "Vim configuration syntax is valid!"
exit 0
""".format(
            config = config.short_path,
        ),
        is_executable = True,
    )
    
    # Create runfiles for testing
    runfiles = ctx.runfiles(files = [config])
    
    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

vim_test = rule(
    implementation = _vim_test_impl,
    attrs = {
        "config": attr.label(
            doc = "The Vim configuration file to test",
            allow_single_file = [".vim"],
            mandatory = True,
        ),
    },
    test = True,
)

# Installation functionality removed