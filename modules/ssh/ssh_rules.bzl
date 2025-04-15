"""Rules for generating SSH configuration files."""

# Define the SshConfigInfo provider to make configuration data strongly typed
SshConfigInfo = provider(
    doc = "Information about SSH configuration",
    fields = {
        "hosts": "Dictionary of host configurations",
        "global_options": "Dictionary of global SSH options",
        "includes": "List of other SSH configs to include",
        "platform_options": "Platform-specific SSH options",
        "variant_options": "Variant-specific options (work, personal, etc.)",
        "raw_hosts": "Raw SSH host configurations to include as-is",
    },
)

def _ssh_config_impl(ctx):
    """Implementation of ssh_config rule."""

    # Process includes first to set up inheritance
    inherited_hosts = {}
    inherited_global_options = {}
    inherited_platform_options = {}
    inherited_variant_options = {}
    inherited_raw_hosts = {}

    # Process includes (nested configs) and inherit their values
    for include in ctx.attr.includes:
        include_info = include[SshConfigInfo]

        # Merge hosts
        for host, host_options in include_info.hosts.items():
            if host not in inherited_hosts:
                inherited_hosts[host] = {}
            for key, value in host_options.items():
                inherited_hosts[host][key] = value

        # Merge global options
        for key, value in include_info.global_options.items():
            inherited_global_options[key] = value

        # Merge platform-specific options
        for platform, platform_opts in include_info.platform_options.items():
            if platform not in inherited_platform_options:
                inherited_platform_options[platform] = {}
            for key, value in platform_opts.items():
                inherited_platform_options[platform][key] = value

        # Merge variant options
        for variant, variant_opts in include_info.variant_options.items():
            if variant not in inherited_variant_options:
                inherited_variant_options[variant] = {}
            for option_type, options in variant_opts.items():
                if option_type not in inherited_variant_options[variant]:
                    inherited_variant_options[variant][option_type] = {}
                if option_type == "hosts":
                    for host, host_options in options.items():
                        if host not in inherited_variant_options[variant][option_type]:
                            inherited_variant_options[variant][option_type][host] = {}
                        for key, value in host_options.items():
                            inherited_variant_options[variant][option_type][host][key] = value
                else:  # global options
                    for key, value in options.items():
                        inherited_variant_options[variant][option_type][key] = value
        
        # Merge raw hosts
        for host, config in include_info.raw_hosts.items():
            inherited_raw_hosts[host] = config

    # Start with inherited values
    hosts = dict(inherited_hosts)
    global_options = dict(inherited_global_options)
    platform_options = dict(inherited_platform_options)
    variant_options = dict(inherited_variant_options)
    raw_hosts = dict(inherited_raw_hosts)

    # Parse and add hosts configuration
    for flat_key, value in ctx.attr.hosts.items():
        parts = flat_key.split(".", 1)
        if len(parts) != 2:
            fail("Host key must be in 'host.option' format: {}".format(flat_key))
        
        host, option = parts
        if host not in hosts:
            hosts[host] = {}
        hosts[host][option] = value

    # Add global options
    for key, value in ctx.attr.global_options.items():
        global_options[key] = value

    # Parse and add platform-specific options
    for flat_key, value in ctx.attr.platform_options.items():
        parts = flat_key.split(".", 1)
        if len(parts) != 2:
            fail("Platform options key must be in 'platform.option' format: {}".format(flat_key))
            
        platform, option = parts
        if platform not in platform_options:
            platform_options[platform] = {}
        platform_options[platform][option] = value

    # Parse and add variant options
    for flat_key, value in ctx.attr.variant_options.items():
        parts = flat_key.split(".", 2)
        if len(parts) != 3:
            fail("Variant options key must be in 'variant.type.key' format: {}".format(flat_key))
            
        variant, option_type, key = parts
        if variant not in variant_options:
            variant_options[variant] = {}
            
        if option_type not in variant_options[variant]:
            variant_options[variant][option_type] = {}
            
        if option_type == "hosts":
            host_parts = key.split(".", 1)
            if len(host_parts) != 2:
                fail("Variant host key must be in 'variant.hosts.host.option' format: {}".format(flat_key))
            
            host, option = host_parts
            if host not in variant_options[variant][option_type]:
                variant_options[variant][option_type][host] = {}
            variant_options[variant][option_type][host][option] = value
        else:  # global
            variant_options[variant][option_type][key] = value

    # Add raw host configurations
    for host, config in ctx.attr.raw_hosts.items():
        raw_hosts[host] = config

    # Create the provider
    config = SshConfigInfo(
        hosts = hosts,
        global_options = global_options,
        includes = ctx.attr.includes,
        platform_options = platform_options,
        variant_options = variant_options,
        raw_hosts = raw_hosts,
    )

    return [config]

ssh_config = rule(
    implementation = _ssh_config_impl,
    attrs = {
        "hosts": attr.string_dict(
            doc = "Dictionary of host configurations (format: 'host.option'='value')",
            default = {},
        ),
        "global_options": attr.string_dict(
            doc = "Dictionary of global SSH options",
            default = {},
        ),
        "includes": attr.label_list(
            doc = "Other ssh_config targets to include",
            default = [],
            providers = [SshConfigInfo],
        ),
        "platform_options": attr.string_dict(
            doc = "Platform-specific options (format: 'platform.option'='value')",
            default = {},
        ),
        "variant_options": attr.string_dict(
            doc = "Variant-specific options (format: 'variant.type.key'='value')",
            default = {},
        ),
        "raw_hosts": attr.string_dict(
            doc = "Raw SSH host configurations to include",
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

def _ssh_config_generator_impl(ctx):
    """Implementation for ssh_config_generator rule that generates an ssh_config file."""

    # Get the SshConfigInfo provider from the config target
    config_info = ctx.attr.config[SshConfigInfo]

    # Determine the platform
    platform = _get_platform_string(ctx)

    # Determine the variant (default to "base" if not specified)
    variant = ctx.attr.variant if ctx.attr.variant else "base"

    # Prepare the output file
    output = ctx.actions.declare_file(ctx.attr.name + ".ssh_config")
    content = []

    # Generate file header
    content.append("# SSH configuration generated by Bazel")
    content.append("# Generated by target: {}".format(ctx.label))
    content.append("# Platform: {}".format(platform))
    if variant != "base":
        content.append("# Variant: {}".format(variant))
    content.append("")

    # Process global options
    if config_info.global_options:
        content.append("# Global options")
        for key, value in config_info.global_options.items():
            content.append("{} {}".format(key, value))
        content.append("")

    # Add platform-specific options
    if platform in config_info.platform_options:
        content.append("# Platform-specific options for {}".format(platform))
        for key, value in config_info.platform_options[platform].items():
            content.append("{} {}".format(key, value))
        content.append("")

    # Add variant-specific global options
    if variant in config_info.variant_options and "global" in config_info.variant_options[variant]:
        content.append("# Variant-specific global options for {}".format(variant))
        for key, value in config_info.variant_options[variant]["global"].items():
            content.append("{} {}".format(key, value))
        content.append("")

    # Include hint for local config
    content.append("# You can add your local configurations in ~/.ssh/config.local")
    content.append("# This file will be included if it exists")
    content.append("Include ~/.ssh/config.local")
    content.append("")

    # Process host configurations
    for host, host_options in config_info.hosts.items():
        content.append("Host {}".format(host))
        for key, value in host_options.items():
            content.append("    {} {}".format(key, value))
        content.append("")

    # Add variant-specific host configurations
    if variant in config_info.variant_options and "hosts" in config_info.variant_options[variant]:
        variant_hosts = config_info.variant_options[variant]["hosts"]
        for host, host_options in variant_hosts.items():
            content.append("# Variant-specific host for {}".format(variant))
            content.append("Host {}".format(host))
            for key, value in host_options.items():
                content.append("    {} {}".format(key, value))
            content.append("")

    # Add raw host configurations
    for host, config_string in config_info.raw_hosts.items():
        content.append("Host {}".format(host))
        content.append(config_string)
        content.append("")

    # Write the file
    ctx.actions.write(
        output = output,
        content = "\n".join(content),
    )

    # Create a runfiles provider
    runfiles = ctx.runfiles(files = [output])

    return [DefaultInfo(files = depset([output]), runfiles = runfiles)]

ssh_config_generator = rule(
    implementation = _ssh_config_generator_impl,
    attrs = {
        "config": attr.label(
            doc = "The ssh_config target to use",
            mandatory = True,
            providers = [SshConfigInfo],
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