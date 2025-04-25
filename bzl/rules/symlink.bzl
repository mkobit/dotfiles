"""
Rules for creating symbolic links.
"""

def _symlink_impl(ctx):
    """Implementation of the symlink rule."""
    # Get the source file
    src = ctx.file.src
    
    # Determine destination path
    dest = ctx.attr.dest
    if not dest:
        dest = ctx.attr.name
    
    # Create a shell script that will create the symlink
    install_script = ctx.actions.declare_file("%s.install.sh" % ctx.attr.name)
    ctx.actions.write(
        output = install_script,
        content = """#!/bin/bash
# Symlink creation script for {name}
$(location //bin:symlink_creator) "{src}" "{dest}"
""".format(
            name = ctx.attr.name,
            src = src.path,
            dest = dest,
        ),
        is_executable = True,
    )
    
    # Return providers
    return [
        DefaultInfo(
            files = depset([install_script]),
            executable = install_script,
            runfiles = ctx.runfiles(files = [src]),
        ),
    ]

# Define the symlink rule
symlink = rule(
    implementation = _symlink_impl,
    attrs = {
        "src": attr.label(
            doc = "Source file for the symlink",
            allow_single_file = True,
            mandatory = True,
        ),
        "dest": attr.string(
            doc = "Destination path (if different from name)",
            default = "",
        ),
    },
    executable = True,
)