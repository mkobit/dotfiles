"""
Core rules for managing dotfiles.
"""

# Define a provider for dotfile configuration
DotfileInfo = provider(
    doc = "Information about a dotfile",
    fields = {
        "name": "Name of the dotfile (without the leading dot)",
        "src": "Source file",
        "dest": "Destination path (where it will be installed)",
        "platform": "Target platform",
        "variant": "Target variant",
    },
)

def _dotfile_impl(ctx):
    """Implementation of the dotfile rule."""
    # Get the source file
    src = ctx.file.src
    
    # Determine destination path
    dest = ctx.attr.dest
    if not dest:
        dest = "~/.%s" % ctx.attr.name
    
    # Create a file with installation information
    info_file = ctx.actions.declare_file("%s.info" % ctx.attr.name)
    ctx.actions.write(
        output = info_file,
        content = """
Dotfile: {name}
Source: {src}
Destination: {dest}
Platform: {platform}
Variant: {variant}
""".format(
            name = ctx.attr.name,
            src = src.path,
            dest = dest,
            platform = ctx.attr.platform,
            variant = ctx.attr.variant,
        ),
    )
    
    # Create a shell script that will install the dotfile
    install_script = ctx.actions.declare_file("%s.install.sh" % ctx.attr.name)
    ctx.actions.write(
        output = install_script,
        content = """#!/bin/bash
# Installation script for {name}
{symlink_creator} "{src}" "{dest}"
""".format(
            name = ctx.attr.name,
            symlink_creator = ctx.executable._symlink_creator.path,
            src = src.path,
            dest = dest,
        ),
        is_executable = True,
    )
    
    # Return providers
    return [
        DefaultInfo(
            files = depset([src, info_file, install_script]),
            executable = install_script,
            runfiles = ctx.runfiles(files=[src, ctx.executable._symlink_creator]),
        ),
        DotfileInfo(
            name = ctx.attr.name,
            src = src,
            dest = dest,
            platform = ctx.attr.platform,
            variant = ctx.attr.variant,
        ),
    ]

# Define the dotfile rule
dotfile = rule(
    implementation = _dotfile_impl,
    attrs = {
        "src": attr.label(
            doc = "Source file for the dotfile",
            allow_single_file = True,
            mandatory = True,
        ),
        "dest": attr.string(
            doc = "Destination path (if different from ~/.name)",
            default = "",
        ),
        "platform": attr.string(
            doc = "Target platform (e.g., 'linux', 'macos', 'windows')",
            default = "",
        ),
        "variant": attr.string(
            doc = "Target variant (e.g., 'work_laptop', 'personal_desktop')",
            default = "",
        ),
        "_symlink_creator": attr.label(
            default = Label("//bin:symlink_creator"),
            executable = True,
            cfg = "exec",
        ),
    },
    executable = True,
)

# Define a rule for creating a dotfile group
def _dotfile_group_impl(ctx):
    """Implementation of the dotfile_group rule."""
    # Collect all dotfiles from dependencies
    dotfiles = []
    for dep in ctx.attr.deps:
        if DotfileInfo in dep:
            dotfiles.append(dep[DotfileInfo])
    
    # Create a manifest file listing all dotfiles
    manifest = ctx.actions.declare_file("%s.manifest" % ctx.attr.name)
    manifest_content = "# Dotfile manifest for %s\n\n" % ctx.attr.name
    for dotfile in dotfiles:
        manifest_content += "- %s: %s -> %s\n" % (dotfile.name, dotfile.src.path, dotfile.dest)
    
    ctx.actions.write(
        output = manifest,
        content = manifest_content,
    )
    
    # Create an installation script
    install_script = ctx.actions.declare_file("%s.install.sh" % ctx.attr.name)
    install_script_content = "#!/bin/bash\n# Installation script for dotfile group %s\n\n" % ctx.attr.name
    
    # Collect runfiles from all dependencies
    all_runfiles = []
    for dep in ctx.attr.deps:
        if DefaultInfo in dep and dep[DefaultInfo].files_to_run and dep[DefaultInfo].files_to_run.executable:
            dep_path = dep[DefaultInfo].files_to_run.executable
            install_script_content += "echo \"Installing %s...\"\n" % dep.label.name
            install_script_content += "if [ -f \"%s\" ]; then\n" % dep_path.path
            install_script_content += "  %s\n" % dep_path.path
            install_script_content += "else\n"
            install_script_content += "  echo \"Error: %s not found\"\n" % dep_path.path
            install_script_content += "fi\n\n"
            all_runfiles.append(dep[DefaultInfo].default_runfiles)
    
    ctx.actions.write(
        output = install_script,
        content = install_script_content,
        is_executable = True,
    )
    
    # Merge all runfiles from dependencies
    merged_runfiles = ctx.runfiles()
    for runfile in all_runfiles:
        merged_runfiles = merged_runfiles.merge(runfile)
    
    # Return both DefaultInfo and DotfileInfo providers
    # This allows dotfile_group rules to be used as deps for other dotfile_group rules
    return [
        DefaultInfo(
            files = depset([manifest]),
            executable = install_script,
            runfiles = merged_runfiles,
        ),
        # Create a DotfileInfo provider for the group
        DotfileInfo(
            name = ctx.attr.name,
            src = manifest,
            dest = "~/.%s" % ctx.attr.name,  # This is a placeholder, not actually used
            platform = "",
            variant = "",
        ),
    ]

# Define the dotfile_group rule
dotfile_group = rule(
    implementation = _dotfile_group_impl,
    attrs = {
        "deps": attr.label_list(
            doc = "List of dotfile targets",
            providers = [DotfileInfo],
        ),
    },
    executable = True,
)