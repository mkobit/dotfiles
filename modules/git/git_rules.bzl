"""Rules for generating Git configuration files."""

# Define the GitConfigInfo provider to make configuration data strongly typed
GitConfigInfo = provider(
    doc = "Information about Git configuration",
    fields = {
        "settings": "Dictionary of git settings organized by section",
        "aliases": "Dictionary of git aliases",
        "includes": "List of other git configs to include",
        "platform_specific": "Platform-specific settings",
        "raw_sections": "Raw git config sections to include",
        "variant_settings": "Variant-specific settings (work, personal, etc.)",
    },
)

def _git_config_impl(ctx):
    """Implementation of git_config rule."""

    # Process includes first to set up inheritance
    inherited_settings = {}
    inherited_aliases = {}
    inherited_platform_settings = {}
    inherited_raw_sections = {}
    inherited_variant_settings = {}

    # Process includes (nested configs) and inherit their values
    for include in ctx.attr.includes:
        include_info = include[GitConfigInfo]

        # Merge settings
        for section, settings in include_info.settings.items():
            if section not in inherited_settings:
                inherited_settings[section] = {}
            for key, value in settings.items():
                inherited_settings[section][key] = value

        # Merge aliases
        for name, command in include_info.aliases.items():
            if name not in inherited_aliases:
                inherited_aliases[name] = command

        # Merge platform-specific settings
        for platform, platform_settings in include_info.platform_specific.items():
            if platform not in inherited_platform_settings:
                inherited_platform_settings[platform] = {}
            for section, settings in platform_settings.items():
                if section not in inherited_platform_settings[platform]:
                    inherited_platform_settings[platform][section] = {}
                for key, value in settings.items():
                    inherited_platform_settings[platform][section][key] = value

        # Merge raw sections
        for section_name, content in include_info.raw_sections.items():
            if section_name not in inherited_raw_sections:
                inherited_raw_sections[section_name] = content

        # Merge variant settings
        for variant, variant_settings in include_info.variant_settings.items():
            if variant not in inherited_variant_settings:
                inherited_variant_settings[variant] = {}
            for section, settings in variant_settings.items():
                if section not in inherited_variant_settings[variant]:
                    inherited_variant_settings[variant][section] = {}
                for key, value in settings.items():
                    inherited_variant_settings[variant][section][key] = value

    # Create dictionaries to hold our configuration, starting with inherited values
    settings = dict(inherited_settings)
    aliases = dict(inherited_aliases)
    platform_settings = dict(inherited_platform_settings)
    raw_sections = dict(inherited_raw_sections)
    variant_settings = dict(inherited_variant_settings)

    # Parse and override with settings from the rule attributes in flat format
    for flat_key, value in ctx.attr.settings.items():
        parts = flat_key.split(".", 1)
        if len(parts) != 2:
            fail("Settings key must be in 'section.key' format: {}".format(flat_key))
        
        section, key = parts
        if section not in settings:
            settings[section] = {}
        settings[section][key] = value

    # Add aliases
    for name, command in ctx.attr.aliases.items():
        aliases[name] = command

    # Parse and add platform-specific settings in flat format
    for flat_key, value in ctx.attr.platform_settings.items():
        parts = flat_key.split(".", 2)
        if len(parts) != 3:
            fail("Platform settings key must be in 'platform.section.key' format: {}".format(flat_key))
            
        platform, section, key = parts
        if platform not in platform_settings:
            platform_settings[platform] = {}
        if section not in platform_settings[platform]:
            platform_settings[platform][section] = {}
        platform_settings[platform][section][key] = value

    # Add raw sections
    for section_name, content in ctx.attr.raw_sections.items():
        raw_sections[section_name] = content

    # Parse and add variant settings in flat format
    for flat_key, value in ctx.attr.variant_settings.items():
        parts = flat_key.split(".", 2)
        if len(parts) != 3:
            fail("Variant settings key must be in 'variant.section.key' format: {}".format(flat_key))
            
        variant, section, key = parts
        if variant not in variant_settings:
            variant_settings[variant] = {}
        if section not in variant_settings[variant]:
            variant_settings[variant][section] = {}
        variant_settings[variant][section][key] = value

    # Create the provider
    config = GitConfigInfo(
        settings = settings,
        aliases = aliases,
        includes = ctx.attr.includes,
        platform_specific = platform_settings,
        raw_sections = raw_sections,
        variant_settings = variant_settings,
    )

    return [config]

git_config = rule(
    implementation = _git_config_impl,
    attrs = {
        "settings": attr.string_dict(
            doc = "Dictionary of git settings by section (flat format: 'section.key'='value')",
            default = {},
        ),
        "aliases": attr.string_dict(
            doc = "Dictionary of git aliases",
            default = {},
        ),
        "includes": attr.label_list(
            doc = "Other git_config targets to include",
            default = [],
            providers = [GitConfigInfo],
        ),
        "platform_settings": attr.string_dict(
            doc = "Platform-specific settings (flat format: 'platform.section.key'='value')",
            default = {},
        ),
        "raw_sections": attr.string_dict(
            doc = "Raw git config sections to include",
            default = {},
        ),
        "variant_settings": attr.string_dict(
            doc = "Variant-specific settings (flat format: 'variant.section.key'='value')",
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

def _git_config_generator_impl(ctx):
    """Implementation for git_config_generator rule that generates a .gitconfig file."""

    # Get the GitConfigInfo provider from the config target
    config_info = ctx.attr.config[GitConfigInfo]

    # Determine the platform
    platform = _get_platform_string(ctx)

    # Determine the variant (default to "base" if not specified)
    variant = ctx.attr.variant if ctx.attr.variant else "base"

    # Prepare the output file
    output = ctx.actions.declare_file(ctx.attr.name + ".gitconfig")
    content = []

    # Generate file header
    content.append("# Generated .gitconfig file - DO NOT EDIT")
    content.append("# Generated by Bazel from {}".format(ctx.label))
    content.append("# Platform: {}".format(platform))
    content.append("# Variant: {}".format(variant))
    content.append("")

    # Log for debugging
    print("Generating gitconfig for variant: {}".format(variant))
    if variant in config_info.variant_settings:
        print("Found variant settings for {}".format(variant))
    else:
        print("No variant settings found for {}".format(variant))
        print("Available variants: {}".format(list(config_info.variant_settings.keys())))

    # Helper function to add a section
    def add_section(section_name, settings_dict):
        section_content = ["[{}]".format(section_name)]
        for key, value in settings_dict.items():
            section_content.append("\t{} = {}".format(key, value))
        section_content.append("")
        return section_content

    # Process base settings
    for section, section_settings in config_info.settings.items():
        content.extend(add_section(section, section_settings))

    # Process aliases in a dedicated section
    if config_info.aliases:
        alias_section = ["[alias]"]
        for name, command in config_info.aliases.items():
            alias_section.append("\t{} = {}".format(name, command))
        alias_section.append("")
        content.extend(alias_section)

    # Add platform-specific settings
    if platform in config_info.platform_specific:
        platform_dict = config_info.platform_specific[platform]
        content.append("# Platform-specific settings for {}".format(platform))
        for section, section_settings in platform_dict.items():
            content.extend(add_section(section, section_settings))

    # Add variant-specific settings
    if variant in config_info.variant_settings:
        variant_dict = config_info.variant_settings[variant]
        content.append("# Variant-specific settings for {}".format(variant))
        for section, section_settings in variant_dict.items():
            content.extend(add_section(section, section_settings))

    # Add raw sections
    for section_name, section_content in config_info.raw_sections.items():
        content.append("[{}]".format(section_name))
        content.append(section_content)
        content.append("")

    # Write the file
    ctx.actions.write(
        output = output,
        content = "\n".join(content),
    )

    # Create a runfiles provider
    runfiles = ctx.runfiles(files = [output])

    return [DefaultInfo(files = depset([output]), runfiles = runfiles)]

git_config_generator = rule(
    implementation = _git_config_generator_impl,
    attrs = {
        "config": attr.label(
            doc = "The git_config target to use",
            mandatory = True,
            providers = [GitConfigInfo],
        ),
        "variant": attr.string(
            doc = "The configuration variant to use (work, personal, etc.)",
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