"""Rules for generating Docker configuration files."""

# Define the DockerConfigInfo provider
DockerConfigInfo = provider(
    doc = "Information about Docker configuration",
    fields = {
        "settings": "Dictionary of Docker settings",
        "includes": "List of other Docker configs to include",
        "platform_specific": "Platform-specific settings",
        "variant_settings": "Variant-specific settings (work, personal, etc.)",
    },
)

def _docker_config_impl(ctx):
    """Implementation of docker_config rule."""

    # Process includes first to set up inheritance
    inherited_settings = {}
    inherited_platform_settings = {}
    inherited_variant_settings = {}

    # Process includes (nested configs) and inherit their values
    for include in ctx.attr.includes:
        include_info = include[DockerConfigInfo]

        # Merge settings
        for key, value in include_info.settings.items():
            inherited_settings[key] = value

        # Merge platform-specific settings
        for platform, platform_settings in include_info.platform_specific.items():
            if platform not in inherited_platform_settings:
                inherited_platform_settings[platform] = {}
            for key, value in platform_settings.items():
                inherited_platform_settings[platform][key] = value

        # Merge variant settings
        for variant, variant_settings in include_info.variant_settings.items():
            if variant not in inherited_variant_settings:
                inherited_variant_settings[variant] = {}
            for key, value in variant_settings.items():
                inherited_variant_settings[variant][key] = value

    # Create dictionaries to hold our configuration
    settings = dict(inherited_settings)
    platform_settings = dict(inherited_platform_settings)
    variant_settings = dict(inherited_variant_settings)

    # Add settings from the rule attributes
    for key, value in ctx.attr.settings.items():
        settings[key] = value

    # Parse and add platform-specific settings
    for flat_key, value in ctx.attr.platform_settings.items():
        parts = flat_key.split(".", 1)
        if len(parts) != 2:
            fail("Platform settings key must be in 'platform.key' format: {}".format(flat_key))
            
        platform, key = parts
        if platform not in platform_settings:
            platform_settings[platform] = {}
        platform_settings[platform][key] = value

    # Parse and add variant settings
    for flat_key, value in ctx.attr.variant_settings.items():
        parts = flat_key.split(".", 1)
        if len(parts) != 2:
            fail("Variant settings key must be in 'variant.key' format: {}".format(flat_key))
            
        variant, key = parts
        if variant not in variant_settings:
            variant_settings[variant] = {}
        variant_settings[variant][key] = value

    # Create the provider
    config = DockerConfigInfo(
        settings = settings,
        includes = ctx.attr.includes,
        platform_specific = platform_settings,
        variant_settings = variant_settings,
    )

    return [config]

docker_config = rule(
    implementation = _docker_config_impl,
    attrs = {
        "settings": attr.string_dict(
            doc = "Dictionary of Docker settings",
            default = {},
        ),
        "includes": attr.label_list(
            doc = "Other docker_config targets to include",
            default = [],
            providers = [DockerConfigInfo],
        ),
        "platform_settings": attr.string_dict(
            doc = "Platform-specific settings (flat format: 'platform.key'='value')",
            default = {},
        ),
        "variant_settings": attr.string_dict(
            doc = "Variant-specific settings (flat format: 'variant.key'='value')",
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
        return "linux"

def _docker_config_generator_impl(ctx):
    """Implementation for docker_config_generator rule that generates configuration files."""

    # Get the DockerConfigInfo provider from the config target
    config_info = ctx.attr.config[DockerConfigInfo]

    # Determine the platform
    platform = _get_platform_string(ctx)

    # Determine the variant (default to "base" if not specified)
    variant = ctx.attr.variant if ctx.attr.variant else "base"

    # Prepare the output file
    output = ctx.actions.declare_file(ctx.attr.name + ".json")
    
    # Build the JSON content
    json_content = {}
    
    # Process base settings
    for key, value in config_info.settings.items():
        json_content[key] = value
        
    # Add platform-specific settings
    if platform in config_info.platform_specific:
        platform_dict = config_info.platform_specific[platform]
        for key, value in platform_dict.items():
            json_content[key] = value
    
    # Add variant-specific settings
    if variant in config_info.variant_settings:
        variant_dict = config_info.variant_settings[variant]
        for key, value in variant_dict.items():
            json_content[key] = value
    
    # Convert to formatted JSON
    import json
    content = json.dumps({
        "debug": False,
        "experimental": True,
        "features": {
            "buildkit": True
        },
        # Add header comments via metadata
        "__metadata__": {
            "generated_by": str(ctx.label),
            "platform": platform,
            "variant": variant,
        }
    }, indent=2)

    # Write the file
    ctx.actions.write(
        output = output,
        content = content,
    )

    # Create a runfiles provider
    runfiles = ctx.runfiles(files = [output])

    return [DefaultInfo(files = depset([output]), runfiles = runfiles)]

docker_config_generator = rule(
    implementation = _docker_config_generator_impl,
    attrs = {
        "config": attr.label(
            doc = "The docker_config target to use",
            mandatory = True,
            providers = [DockerConfigInfo],
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