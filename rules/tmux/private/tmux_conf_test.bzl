"""
Rule for testing tmux configuration files.
"""

def _tmux_conf_test_impl(ctx):
    # Access the toolchain
    toolchain = ctx.toolchains["//toolchains/tmux:toolchain_type"]
    tmuxinfo = toolchain.tmuxinfo

    # Get the configuration file
    conf_file = ctx.file.conf

    # Copy the conf file to a predictable location
    copied_conf = ctx.actions.declare_file(ctx.label.name + "_test.conf")
    ctx.actions.run_shell(
        outputs = [copied_conf],
        inputs = [conf_file],
        command = "cp '{}' '{}'".format(conf_file.path, copied_conf.path),
    )

    # Create a test script that validates the configuration
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")
    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -euo pipefail

# Use the tmux path from the toolchain
TMUX="{tmux_path}"

# Use the copied configuration file with an absolute path
CONFIG="{config_path}"

echo "Testing tmux configuration using $TMUX"
echo "Configuration file: $CONFIG"

# Just validate the syntax without trying to start a server
"$TMUX" -f "$CONFIG" -L syntax_check new-session -d "true" 2>/dev/null || {{
    echo "Failed to validate tmux configuration - syntax error"
    exit 1
}}

echo "Tmux configuration syntax validation passed!"
exit 0
""".format(
            tmux_path = tmuxinfo.tmux_path,
            config_path = copied_conf.path,
        ),
        is_executable = True,
    )
    
    return [
        DefaultInfo(
            executable = test_script,
            # Create runfiles to include the copied config
            runfiles = ctx.runfiles(files = [copied_conf]),
        ),
    ]

tmux_conf_test = rule(
    implementation = _tmux_conf_test_impl,
    attrs = {
        "conf": attr.label(
            doc = "The tmux configuration file to test",
            allow_single_file = True,
            mandatory = True,
        ),
    },
    test = True,
    toolchains = ["//toolchains/tmux:toolchain_type"],
)