"""Rules for generating Vim configuration files."""

# Define the VimConfigInfo provider to make configuration data strongly typed
VimConfigInfo = provider(
    doc = "Information about Vim configuration",
    fields = {
        "settings": "Dictionary of vim settings",
        "plugins": "List of vim plugins to include",
        "includes": "List of other vim configs to include",
        "platform_specific": "Platform-specific settings",
        "raw_statements": "Raw Vim script statements to include",
        "mappings": "Keyboard mappings to include",
    },
)

def _normalize_bool_setting(value):
    """Normalize boolean settings to Vim syntax."""
    if value == True:
        return "set"
    elif value == False:
        return "set no"
    return value

def _vim_config_impl(ctx):
    """Implementation of vim_config rule."""
    # Process includes first to set up inheritance
    inherited_settings = {}
    inherited_plugins = []
    inherited_platform_settings = {}
    inherited_raw_statements = []
    inherited_mappings = {}
    
    # Process includes (nested configs) and inherit their values
    for include in ctx.attr.includes:
        include_info = include[VimConfigInfo]
        # Merge settings
        for key, value in include_info.settings.items():
            if key not in inherited_settings:
                inherited_settings[key] = value
        
        # Merge plugins
        for plugin in include_info.plugins:
            if plugin not in inherited_plugins:
                inherited_plugins.append(plugin)
        
        # Merge platform-specific settings
        for platform, settings_list in include_info.platform_specific.items():
            if platform not in inherited_platform_settings:
                inherited_platform_settings[platform] = []
            inherited_platform_settings[platform].extend(settings_list)
        
        # Merge raw statements
        if hasattr(include_info, "raw_statements") and include_info.raw_statements:
            inherited_raw_statements.extend(include_info.raw_statements)
        
        # Merge mappings
        if hasattr(include_info, "mappings") and include_info.mappings:
            for key, mapping in include_info.mappings.items():
                if key not in inherited_mappings:
                    inherited_mappings[key] = mapping
    
    # Create a dictionary to hold our configuration, starting with inherited values
    settings = dict(inherited_settings)
    
    # Override with settings from the rule attributes
    for key, value in ctx.attr.settings.items():
        settings[key] = value
    
    # Handle platform-specific settings
    platform_settings = dict(inherited_platform_settings)
    for platform, platform_list in ctx.attr.platform_settings.items():
        if platform not in platform_settings:
            platform_settings[platform] = []
        platform_settings[platform].extend(platform_list)
    
    # Combine plugins
    plugins = list(inherited_plugins)
    for plugin in ctx.attr.plugins:
        if plugin not in plugins:
            plugins.append(plugin)
    
    # Add raw statements
    raw_statements = list(inherited_raw_statements)
    for stmt in ctx.attr.raw_statements:
        raw_statements.append(stmt)
    
    # Add mappings
    mappings = dict(inherited_mappings)
    for key, mapping in ctx.attr.mappings.items():
        mappings[key] = mapping

    # Create the provider
    config = VimConfigInfo(
        settings = settings,
        plugins = plugins,
        includes = ctx.attr.includes,
        platform_specific = platform_settings,
        raw_statements = raw_statements,
        mappings = mappings,
    )
    
    return [config]

vim_config = rule(
    implementation = _vim_config_impl,
    attrs = {
        "settings": attr.string_dict(
            doc = "Dictionary of vim settings",
            default = {},
        ),
        "plugins": attr.string_list(
            doc = "List of vim plugins to include",
            default = [],
        ),
        "includes": attr.label_list(
            doc = "Other vim_config targets to include",
            default = [],
            providers = [VimConfigInfo],
        ),
        "platform_settings": attr.string_list_dict(
            doc = "Platform-specific settings",
            default = {},
        ),
        "raw_statements": attr.string_list(
            doc = "Raw Vim script statements to include",
            default = [],
        ),
        "mappings": attr.string_dict(
            doc = "Keyboard mappings to include (key to command)",
            default = {},
        ),
    },
)

def _get_platform_string(ctx):
    """Determine the current platform."""
    if ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo]):
        return "windows"
    elif ctx.target_platform_has_constraint(ctx.attr._macos_constraint[platform_common.ConstraintValueInfo]):
        return "macos"
    else:
        return "linux"  # Default to Linux

def _vim_config_generator_impl(ctx):
    """Implementation for vim_config_generator rule that generates a .vimrc file."""
    # Get the VimConfigInfo provider from the config target
    config_info = ctx.attr.config[VimConfigInfo]
    
    # Determine the platform
    platform = _get_platform_string(ctx)
    
    # Prepare the output file
    output = ctx.actions.declare_file(ctx.attr.name + ".vimrc")
    content = []

    # Generate file header
    content.append('""" Generated .vimrc file - DO NOT EDIT """')
    content.append('""" Generated by Bazel from {}"""'.format(ctx.label))
    content.append('""" Platform: {} """'.format(platform))
    content.append('""" Generated on: {} """'.format(ctx.attr.timestamp or "unknown"))
    content.append("")

    # Add basic configurations
    content.append('" Basic Settings')
    for key, value in config_info.settings.items():
        # Handle string-based boolean values
        if value == "true":
            content.append('set {}'.format(key))
        elif value == "false":
            content.append('set no{}'.format(key))
        else:
            # Handle other values
            content.append('set {}={}'.format(key, value))

    # Add platform-specific settings
    if platform in config_info.platform_specific:
        content.append('')
        content.append('" Platform-specific settings for {}'.format(platform))
        for setting in config_info.platform_specific[platform]:
            content.append(setting)

    # Add mappings
    if hasattr(config_info, "mappings") and config_info.mappings:
        content.append('')
        content.append('" Key Mappings')
        for key, mapping in config_info.mappings.items():
            content.append('map {} {}'.format(key, mapping))
    
    # Add raw statements
    if hasattr(config_info, "raw_statements") and config_info.raw_statements:
        content.append('')
        content.append('" Custom Configurations')
        for stmt in config_info.raw_statements:
            content.append(stmt)

    # Add plugin configurations
    if config_info.plugins:
        content.append('')
        content.append('" Plugins')
        if ctx.attr.plugin_manager:
            content.append('" Using plugin manager: {}'.format(ctx.attr.plugin_manager))
            
        for plugin in config_info.plugins:
            if ctx.attr.plugin_manager == "vim-plug":
                content.append('Plug "{}"'.format(plugin))
            elif ctx.attr.plugin_manager == "vundle":
                content.append('Plugin "{}"'.format(plugin))
            else:
                # Default format for plugins
                content.append('" {}'.format(plugin))
    
    # Add validation marker for tests
    content.append('')
    content.append('" Validation marker: DO NOT REMOVE')
    content.append('" vim_config_id: {}'.format(ctx.label))

    # Write the file
    ctx.actions.write(
        output = output,
        content = "\n".join(content),
    )
    
    # Create a runfiles provider if we need to include additional files
    runfiles = ctx.runfiles(files = [output])
    
    return [DefaultInfo(files = depset([output]), runfiles = runfiles)]

vim_config_generator = rule(
    implementation = _vim_config_generator_impl,
    attrs = {
        "config": attr.label(
            doc = "The vim_config target to use",
            mandatory = True,
            providers = [VimConfigInfo],
        ),
        "plugin_manager": attr.string(
            doc = "Plugin manager to use (vim-plug, vundle, etc.)",
            default = "vundle",
        ),
        "timestamp": attr.string(
            doc = "Timestamp for generation (defaults to build time)",
            default = "",
        ),
        # Platform constraints
        "_windows_constraint": attr.label(
            default = "@platforms//os:windows",
        ),
        "_macos_constraint": attr.label(
            default = "@platforms//os:macos",
        ),
        "_linux_constraint": attr.label(
            default = "@platforms//os:linux",
        ),
    },
)

def _vim_test_impl(ctx):
    """Implementation of vim_test rule."""
    # Get the input .vimrc file
    vimrc = ctx.file.vimrc
    
    # Create a test script
    script = ctx.actions.declare_file("{}_test.sh".format(ctx.attr.name))
    
    # Command to validate the vimrc - simplified version
    cmd = [
        "#!/bin/bash",
        "set -euo pipefail",
        "",
        "echo 'Running test: {}'".format(ctx.attr.name),
        "echo 'Testing file: {}'".format(vimrc.short_path),
        "",
        "# Test file existence",
        "if [ ! -f '{}' ]; then".format(vimrc.short_path),
        "  echo 'ERROR: .vimrc file not found'",
        "  exit 1",
        "fi",
        "",
        "# Print file content for debugging",
        "echo 'File content:'",
        "echo '----------------------------------------'",
        "cat '{}'".format(vimrc.short_path),
        "echo '----------------------------------------'",
        "",
        "# Validate required content",
    ]
    
    # Add validation commands based on requirements
    for i, req in enumerate(ctx.attr.requirements):
        escaped_req = req.replace("'", "\\'").replace('"', '\\"')
        cmd.append("echo 'Checking for required string {}: {}'".format(i+1, escaped_req))
        cmd.append("if ! grep -q '{}' '{}'; then".format(escaped_req, vimrc.short_path))
        cmd.append("  echo 'ERROR: Required setting not found: {}'".format(escaped_req))
        cmd.append("  exit 1")
        cmd.append("fi")
    
    # Check for prohibited content
    if ctx.attr.prohibited:
        cmd.append("")
        cmd.append("# Validate prohibited content")
        for i, prohibited in enumerate(ctx.attr.prohibited):
            escaped_prohibited = prohibited.replace("'", "\\'").replace('"', '\\"')
            cmd.append("echo 'Checking for prohibited string {}: {}'".format(i+1, escaped_prohibited))
            cmd.append("if grep -q '{}' '{}'; then".format(escaped_prohibited, vimrc.short_path))
            cmd.append("  echo 'ERROR: Prohibited setting found: {}'".format(escaped_prohibited))
            cmd.append("  exit 1")
            cmd.append("fi")
    
    # Final success message
    cmd.extend([
        "",
        "echo 'All tests passed for {}'".format(ctx.attr.name),
        "exit 0",
    ])
    
    # Write the test script
    ctx.actions.write(
        output = script,
        content = "\n".join(cmd),
        is_executable = True,
    )
    
    # Create a runfiles object with all necessary files
    runfiles = ctx.runfiles(files = [vimrc])
    
    # Return the executable and runfiles
    return [
        DefaultInfo(
            executable = script,
            runfiles = runfiles,
        ),
    ]

vim_test = rule(
    implementation = _vim_test_impl,
    attrs = {
        "vimrc": attr.label(
            doc = "The .vimrc file to test",
            allow_single_file = True,
            mandatory = True,
        ),
        "requirements": attr.string_list(
            doc = "List of required strings in the .vimrc",
            default = [],
        ),
        "prohibited": attr.string_list(
            doc = "List of prohibited strings in the .vimrc",
            default = [],
        ),
    },
    test = True,
)