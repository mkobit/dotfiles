"""
Common utilities for toolchain implementations.

This module provides reusable functions and patterns for creating
toolchains that discover tools locally. Tools must be installed -
no mock implementations.
"""

def create_tool_info_provider(tool_name, fields = None):
    """Creates a provider for tool information.

    Args:
        tool_name: Name of the tool (e.g., "tmux", "git", "zsh")
        fields: Optional dict of additional fields beyond the standard ones

    Returns:
        A provider with standard fields plus any additional ones
    """
    standard_fields = {
        "{}_path".format(tool_name): "Path to the {} executable".format(tool_name),
        "{}_version".format(tool_name): "Version of {} being used".format(tool_name),
        "env": "Environment variables to set when invoking {}".format(tool_name),
    }

    if fields:
        standard_fields.update(fields)

    return provider(
        doc = "Information about how to invoke the {} executable.".format(tool_name),
        fields = standard_fields,
    )

def create_toolchain_rule(tool_name, provider_info, additional_attrs = None):
    """Creates a toolchain rule for a tool.

    Args:
        tool_name: Name of the tool
        provider_info: The provider created by create_tool_info_provider
        additional_attrs: Optional dict of additional attributes

    Returns:
        A toolchain rule implementation
    """
    def _impl(ctx):
        tool_path_attr = "{}_path".format(tool_name)
        version_attr = "{}_version".format(tool_name)

        info_kwargs = {
            tool_path_attr: getattr(ctx.attr, tool_path_attr),
            version_attr: getattr(ctx.attr, version_attr, "unknown"),
            "env": ctx.attr.env,
        }

        # Add any additional fields from attributes
        if additional_attrs:
            for attr_name in additional_attrs:
                if hasattr(ctx.attr, attr_name):
                    info_kwargs[attr_name] = getattr(ctx.attr, attr_name)

        toolchain_info = platform_common.ToolchainInfo(
            **{tool_name + "info": provider_info(**info_kwargs)}
        )
        return [toolchain_info]

    standard_attrs = {
        "{}_path".format(tool_name): attr.string(
            doc = "Path to the {} executable".format(tool_name),
            mandatory = True,
        ),
        "{}_version".format(tool_name): attr.string(
            doc = "Version of {} being used".format(tool_name),
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when invoking {}".format(tool_name),
            default = {},
        ),
    }

    if additional_attrs:
        standard_attrs.update(additional_attrs)

    return rule(
        implementation = _impl,
        attrs = standard_attrs,
    )

def create_local_tool_repository_rule(tool_name, version_flag = "-V"):
    """Creates a repository rule for discovering a tool locally.

    Args:
        tool_name: Name of the tool
        version_flag: Flag to get version info

    Returns:
        A repository rule that discovers the tool locally
    """
    def _impl(repository_ctx):
        # Find tool binary in the path - fail if not found
        tool_path = repository_ctx.which(tool_name)

        if not tool_path:
            fail("ERROR: {} not found in PATH. Please install {} before building.\n".format(tool_name, tool_name) +
                 "Installation instructions:\n" +
                 "  macOS: brew install {}\n".format(tool_name) +
                 "  Ubuntu/Debian: sudo apt-get install {}\n".format(tool_name) +
                 "  Or check your package manager for {} installation.".format(tool_name))

        # Get version from real binary
        result = repository_ctx.execute([tool_path, version_flag])
        if result.return_code != 0:
            version = "unknown"
        else:
            version_output = result.stdout.strip()
            # Default: extract second word from version output like "tmux 3.2a"
            parts = version_output.split(" ")
            version = parts[1] if len(parts) > 1 else "unknown"

        # Determine platform constraints
        os = repository_ctx.os.name
        exec_constraints = []
        target_constraints = []

        if os.startswith("mac"):
            exec_constraints = ["@platforms//os:macos"]
            target_constraints = ["@platforms//os:macos"]
        elif os.startswith("linux"):
            exec_constraints = ["@platforms//os:linux"]
            target_constraints = ["@platforms//os:linux"]

        # Format constraints for BUILD file
        exec_constraints_formatted = ""
        for c in exec_constraints:
            exec_constraints_formatted += '        "{}",\n'.format(c)

        target_constraints_formatted = ""
        for c in target_constraints:
            target_constraints_formatted += '        "{}",\n'.format(c)

        # Create the BUILD file with toolchain definition
        repository_ctx.file("BUILD.bazel", '''
package(default_visibility = ["//visibility:public"])

load("@dotfiles//toolchains/{tool_name}:toolchain.bzl", "{tool_name}_toolchain")

{tool_name}_toolchain(
    name = "{tool_name}_local_impl",
    {tool_name}_path = "{tool_path}",
    {tool_name}_version = "{version}",
)

toolchain(
    name = "{tool_name}_local",
    exec_compatible_with = [
{exec_constraints}    ],
    target_compatible_with = [
{target_constraints}    ],
    toolchain = ":{tool_name}_local_impl",
    toolchain_type = "@dotfiles//toolchains/{tool_name}:toolchain_type",
)
'''.format(
            tool_name = tool_name,
            tool_path = tool_path,
            version = version,
            exec_constraints = exec_constraints_formatted,
            target_constraints = target_constraints_formatted,
        ))

    return repository_rule(
        implementation = _impl,
        doc = "Creates a repository that discovers the local {} installation".format(tool_name),
    )
