"""Rules for generating Neovim configuration files."""

# Define the NeovimConfigInfo provider to make configuration data strongly typed
NeovimConfigInfo = provider(
    doc = "Information about Neovim configuration",
    fields = {
        "settings": "Dictionary of neovim settings",
        "plugins": "List of neovim plugins to include",
        "includes": "List of other neovim configs to include",
        "platform_specific": "Platform-specific settings",
        "raw_statements": "Raw Neovim Lua statements to include",
        "mappings": "Keyboard mappings to include",
        "lua_config": "Lua configuration code",
    },
)

def _normalize_bool_setting(value):
    """Normalize boolean settings to Vim/Neovim syntax."""
    if value == True:
        return "set"
    elif value == False:
        return "set no"
    return value

def _neovim_config_impl(ctx):
    """Implementation of neovim_config rule."""

    # Process includes first to set up inheritance
    inherited_settings = {}
    inherited_platform_settings = {}
    inherited_raw_statements = []
    inherited_mappings = {}
    inherited_lua_config = []

    # Process includes (nested configs) and inherit their values
    for include in ctx.attr.includes:
        include_info = include[NeovimConfigInfo]

        # Merge settings
        for key, value in include_info.settings.items():
            if key not in inherited_settings:
                inherited_settings[key] = value

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

        # Merge Lua configs
        if hasattr(include_info, "lua_config") and include_info.lua_config:
            inherited_lua_config.extend(include_info.lua_config)

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

    # Add raw statements
    raw_statements = list(inherited_raw_statements)
    for stmt in ctx.attr.raw_statements:
        raw_statements.append(stmt)

    # Add mappings
    mappings = dict(inherited_mappings)
    for key, mapping in ctx.attr.mappings.items():
        mappings[key] = mapping

    # Add lua configs
    lua_config = list(inherited_lua_config)
    for lua_code in ctx.attr.lua_config:
        lua_config.append(lua_code)

    # Create the provider
    config = NeovimConfigInfo(
        settings = settings,
        includes = ctx.attr.includes,
        platform_specific = platform_settings,
        raw_statements = raw_statements,
        mappings = mappings,
        lua_config = lua_config,
    )

    return [config]

neovim_config = rule(
    implementation = _neovim_config_impl,
    attrs = {
        "settings": attr.string_dict(
            doc = "Dictionary of neovim settings",
            default = {},
        ),
        "includes": attr.label_list(
            doc = "Other neovim_config targets to include",
            default = [],
            providers = [NeovimConfigInfo],
        ),
        "platform_settings": attr.string_list_dict(
            doc = "Platform-specific settings",
            default = {},
        ),
        "raw_statements": attr.string_list(
            doc = "Raw Neovim script statements to include",
            default = [],
        ),
        "mappings": attr.string_dict(
            doc = "Keyboard mappings to include (key to command)",
            default = {},
        ),
        "lua_config": attr.string_list(
            doc = "Lua configuration statements",
            default = [],
        ),
    }
)

def _get_platform_string(ctx):
    """Determine the current platform."""
    if ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo]):
        return "windows"
    elif ctx.target_platform_has_constraint(ctx.attr._macos_constraint[platform_common.ConstraintValueInfo]):
        return "macos"
    else:
        return "linux"  # Default to Linux

def _neovim_config_generator_impl(ctx):
    """Implementation for neovim_config_generator rule that generates init.lua and init.vim files."""

    # Get the NeovimConfigInfo provider from the config target
    config_info = ctx.attr.config[NeovimConfigInfo]

    # Determine the platform
    platform = _get_platform_string(ctx)

    # Get output filenames
    vim_filename = ctx.attr.outs[0] if ctx.attr.outs and len(ctx.attr.outs) > 0 else "init.vim"
    lua_filename = ctx.attr.outs[1] if ctx.attr.outs and len(ctx.attr.outs) > 1 else "init.lua"

    # Prepare the VimL output file
    vim_output = ctx.actions.declare_file(vim_filename)
    vim_content = []

    # Generate file header
    vim_content.append('""" Generated init.vim file - DO NOT EDIT """')
    vim_content.append('""" Generated by Bazel from {}"""'.format(ctx.label))
    vim_content.append('""" Platform: {} """'.format(platform))
    vim_content.append("")
    
    # Add VimL settings
    vim_content.append('" Basic Settings')
    for key, value in config_info.settings.items():
        # Skip settings that are handled in Lua
        if ctx.attr.lua_mode and key.startswith("lua_"):
            continue
            
        # Handle string-based boolean values
        if value == "true":
            vim_content.append("set {}".format(key))
        elif value == "false":
            vim_content.append("set no{}".format(key))
        else:
            # Handle other values
            vim_content.append("set {}={}".format(key, value))

    # Add platform-specific settings for VimL
    if platform in config_info.platform_specific:
        vim_content.append("")
        vim_content.append('" Platform-specific settings for {}'.format(platform))
        for setting in config_info.platform_specific[platform]:
            if not setting.startswith("lua_"):
                vim_content.append(setting)

    # Add mappings (VimL style)
    if hasattr(config_info, "mappings") and config_info.mappings:
        vim_content.append("")
        vim_content.append('" Key Mappings')
        for key, mapping in config_info.mappings.items():
            vim_content.append("map {} {}".format(key, mapping))

    # Add raw statements (VimL)
    if hasattr(config_info, "raw_statements") and config_info.raw_statements:
        vim_content.append("")
        vim_content.append('" Custom Configurations')
        for stmt in config_info.raw_statements:
            if not stmt.startswith("lua_"):
                vim_content.append(stmt)

    # Write the VimL file
    ctx.actions.write(
        output = vim_output,
        content = "\n".join(vim_content),
    )

    # Prepare the Lua output file if in Lua mode
    outputs = [vim_output]
    if ctx.attr.lua_mode:
        lua_output = ctx.actions.declare_file(lua_filename)
        lua_content = []
        
        # Generate Lua file header
        lua_content.append("-- Generated init.lua file - DO NOT EDIT")
        lua_content.append("-- Generated by Bazel from " + str(ctx.label))
        lua_content.append("-- Platform: " + platform)
        lua_content.append("")
        
        # Add Vim options (using vim.opt in Lua)
        lua_content.append("-- Basic Settings")
        for key, value in config_info.settings.items():
            if key.startswith("lua_"):
                # Handle native Lua settings (strip the lua_ prefix)
                lua_key = key[4:]  # Remove "lua_" prefix
                if value == "true":
                    lua_content.append("vim.opt.{} = true".format(lua_key))
                elif value == "false":
                    lua_content.append("vim.opt.{} = false".format(lua_key))
                else:
                    # Try to detect if value is a number
                    if value.isdigit():
                        lua_content.append("vim.opt.{} = {}".format(lua_key, value))
                    else:
                        lua_content.append("vim.opt.{} = \"{}\"".format(lua_key, value))
        
        # Add platform-specific settings for Lua
        if platform in config_info.platform_specific:
            lua_content.append("")
            lua_content.append("-- Platform-specific settings for " + platform)
            for setting in config_info.platform_specific[platform]:
                if setting.startswith("lua_"):
                    lua_content.append(setting[4:])  # Strip "lua_" prefix
        
        # Add Lua configurations
        if hasattr(config_info, "lua_config") and config_info.lua_config:
            lua_content.append("")
            lua_content.append("-- Lua Custom Configurations")
            for code in config_info.lua_config:
                lua_content.append(code)
        
        # Write the Lua file
        ctx.actions.write(
            output = lua_output,
            content = "\n".join(lua_content),
        )
        outputs.append(lua_output)

    # Create a runfiles provider
    runfiles = ctx.runfiles(files = outputs)

    return [DefaultInfo(files = depset(outputs), runfiles = runfiles)]

neovim_config_generator = rule(
    implementation = _neovim_config_generator_impl,
    attrs = {
        "config": attr.label(
            doc = "The neovim_config target to use",
            mandatory = True,
            providers = [NeovimConfigInfo],
        ),
        "lua_mode": attr.bool(
            doc = "Generate Lua configurations in addition to VimL",
            default = True,
        ),
        "outs": attr.string_list(
            doc = "Output file names. First is VimL, second is Lua if lua_mode is True",
            default = ["init.vim", "init.lua"],
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
    }
)