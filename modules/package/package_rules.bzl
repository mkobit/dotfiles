"""Rules for managing packages across different package managers."""

load("//modules/toolchains:toolchain_utils.bzl", "brew_path")

# Provider for package configuration
PackageInfo = provider(
    doc = "Information about packages to be installed",
    fields = {
        "packages": "List of packages to install",
        "casks": "List of casks to install (for brew)",
        "taps": "List of taps to add (for brew)",
        "manager": "Package manager to use (brew, apt, etc.)",
        "options": "Additional options for package installation",
    },
)

def _package_config_impl(ctx):
    return [
        PackageInfo(
            packages = ctx.attr.packages,
            casks = ctx.attr.casks,
            taps = ctx.attr.taps,
            manager = ctx.attr.manager,
            options = ctx.attr.options,
        ),
    ]

package_config = rule(
    implementation = _package_config_impl,
    attrs = {
        "packages": attr.string_list(default = [], doc = "List of packages to install"),
        "casks": attr.string_list(default = [], doc = "List of casks to install (for brew)"),
        "taps": attr.string_list(default = [], doc = "List of taps to add (for brew)"),
        "manager": attr.string(default = "brew", doc = "Package manager to use"),
        "options": attr.string_dict(default = {}, doc = "Additional options for installation"),
    },
)

def _generate_package_manifest_impl(ctx):
    brew_path_result = brew_path(ctx)
    config = ctx.attr.config[PackageInfo]
    
    output_content = ""
    
    # Check if brew is available - generate a warning script if not available
    if not brew_path_result:
        output_content = """#!/bin/bash
        
# WARNING: Brew is not available in this environment
# This is a placeholder script for package installation

echo "WARNING: Brew is not available in this environment"
echo "This script would normally install packages with brew"
echo "Please install brew and re-run this build"
exit 0
"""
        # Write the manifest file
        out = ctx.actions.declare_file(ctx.attr.name + ".sh")
        ctx.actions.write(
            output = out,
            content = output_content,
            is_executable = True,
        )
        return [DefaultInfo(
            files = depset([out]),
            executable = out,
        )]
    
    # Generate manifest content based on package manager
    if config.manager == "brew":
        # Generate brew manifest
        output_content += "#!/bin/bash\n\n"
        output_content += "# Generated Homebrew package manifest\n"
        output_content += "# This script installs all required packages\n\n"
        output_content += "set -e\n\n"
        
        # Check for brew installation
        output_content += "if ! command -v brew &> /dev/null; then\n"
        output_content += "    echo \"Homebrew not installed. Please install Homebrew first.\"\n"
        output_content += "    exit 1\n"
        output_content += "fi\n\n"
        
        # Add taps
        if config.taps:
            output_content += "# Add taps\n"
            output_content += "echo \"Adding taps...\"\n"
            for tap in config.taps:
                output_content += "brew tap {}\n".format(tap)
            output_content += "\n"
        
        # Update brew
        output_content += "# Update Homebrew\n"
        output_content += "echo \"Updating Homebrew...\"\n"
        output_content += "brew update\n\n"
        
        # Install packages
        if config.packages:
            output_content += "# Install packages\n"
            output_content += "echo \"Installing packages...\"\n"
            output_content += "brew install \\\n"
            for pkg in config.packages[:-1]:
                output_content += "    {} \\\n".format(pkg)
            output_content += "    {}\n\n".format(config.packages[-1])
        
        # Install casks
        if config.casks:
            output_content += "# Install casks\n"
            output_content += "echo \"Installing casks...\"\n"
            output_content += "brew install --cask \\\n"
            for cask in config.casks[:-1]:
                output_content += "    {} \\\n".format(cask)
            output_content += "    {}\n\n".format(config.casks[-1])
        
        output_content += "echo \"All packages installed successfully!\"\n"
    else:
        fail("Unsupported package manager: {}".format(config.manager))
    
    # Write the manifest file
    out = ctx.actions.declare_file(ctx.attr.name + ".sh")
    ctx.actions.write(
        output = out,
        content = output_content,
        is_executable = True,
    )
    
    return [DefaultInfo(
        files = depset([out]),
        executable = out,
    )]

generate_package_manifest = rule(
    implementation = _generate_package_manifest_impl,
    attrs = {
        "config": attr.label(
            mandatory = True,
            providers = [PackageInfo],
            doc = "Package configuration",
        ),
    },
    executable = True,
)

def _print_package_paths_impl(ctx):
    output_script_content = """#!/bin/bash

echo "Package manifest: {}"
""".format(ctx.executable.manifest.short_path)

    out = ctx.actions.declare_file(ctx.attr.name + ".sh")
    ctx.actions.write(
        output = out,
        content = output_script_content,
        is_executable = True,
    )

    return [DefaultInfo(
        files = depset([out]),
        executable = out,
        runfiles = ctx.runfiles(files = [ctx.executable.manifest]),
    )]

print_package_paths = rule(
    implementation = _print_package_paths_impl,
    attrs = {
        "manifest": attr.label(
            mandatory = True,
            executable = True,
            cfg = "exec",
            doc = "Package manifest file",
        ),
    },
    executable = True,
)