"""
Common utilities for toolchain implementations.

This module provides reusable functions and patterns for creating
toolchains that discover tools locally or from dependencies.
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
        "is_mock": "Whether this is a mock implementation",
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
            "is_mock": ctx.attr.is_mock,
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
        "is_mock": attr.bool(
            doc = "Whether this is a mock implementation",
            default = False,
        ),
    }

    if additional_attrs:
        standard_attrs.update(additional_attrs)

    return rule(
        implementation = _impl,
        attrs = standard_attrs,
    )

def create_mock_script_content(tool_name, version_flag = "-V", version_output_format = "{} mock-version"):
    """Creates standard mock script content for a tool.

    Args:
        tool_name: Name of the tool
        version_flag: Flag to get version (default: -V)
        version_output_format: Format string for version output

    Returns:
        String content for the mock script
    """
    return '''#!/bin/bash
echo "MOCK {tool_upper}: This is a mock {tool_name} implementation for building without {tool_name} installed"
echo "MOCK {tool_upper}: Command: $@"

# Handle version request
if [ "$1" = "{version_flag}" ]; then
    echo "{version_output}"
    exit 0
fi

# Handle common validation patterns
case "$*" in
    *"syntax"*|*"check"*|*"validate"*)
        echo "MOCK {tool_upper}: Configuration validation"
        # Always succeed for syntax validation
        exit 0
        ;;
esac

# By default succeed with a warning
echo "MOCK {tool_upper}: This mock implementation has limited functionality"
echo "MOCK {tool_upper}: Real {tool_name} is required for full functionality"
exit 0
'''.format(
        tool_name = tool_name,
        tool_upper = tool_name.upper(),
        version_flag = version_flag,
        version_output = version_output_format.format(tool_name),
    )

def create_local_tool_repository_rule(tool_name, version_flag = "-V", version_regex = None):
    """Creates a repository rule for discovering a tool locally.

    Args:
        tool_name: Name of the tool
        version_flag: Flag to get version info
        version_regex: Optional regex to extract version from output

    Returns:
        A repository rule that discovers the tool locally
    """
    def _impl(repository_ctx):
        # Find tool binary in the path
        tool_path = repository_ctx.which(tool_name)
        is_mock = False

        if not tool_path:
            # Create a mock script if real binary isn't available
            is_mock = True
            mock_script_content = create_mock_script_content(tool_name, version_flag)
            mock_script_path = repository_ctx.path("mock_{}.sh".format(tool_name))
            repository_ctx.file(mock_script_path, mock_script_content, executable = True)
            tool_path = str(mock_script_path)
            version = "mock-version"
        else:
            # Get version from real binary
            result = repository_ctx.execute([tool_path, version_flag])
            if result.return_code != 0:
                is_mock = True
                version = "unknown-version"
            else:
                version_output = result.stdout.strip()
                if version_regex:
                    # TODO: Add regex extraction support
                    version = version_output
                else:
                    # Default: extract second word from version output
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
        implementation_type = "mock_{}_toolchain".format(tool_name) if is_mock else "{}_toolchain".format(tool_name)
        toolchain_bzl_path = "@dotfiles//toolchains/{}:toolchain.bzl".format(tool_name)
        mock_bzl_path = "@dotfiles//toolchains/{}:mock_toolchain.bzl".format(tool_name)

        load_statement = ('load("{}", "{}")'.format(mock_bzl_path, implementation_type)
                          if is_mock else
                          'load("{}", "{}")'.format(toolchain_bzl_path, implementation_type))

        # Create different BUILD content for mock vs real toolchains
        if is_mock:
            build_content = '''
package(default_visibility = ["//visibility:public"])

{load_statement}

{implementation_type}(
    name = "{tool_name}_local_impl",
    mock_path = "{tool_path}",
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
                load_statement = load_statement,
                implementation_type = implementation_type,
                tool_name = tool_name,
                tool_path = tool_path,
                exec_constraints = exec_constraints_formatted,
                target_constraints = target_constraints_formatted,
            )
        else:
            build_content = '''
package(default_visibility = ["//visibility:public"])

{load_statement}

{implementation_type}(
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
                load_statement = load_statement,
                implementation_type = implementation_type,
                tool_name = tool_name,
                tool_path = tool_path,
                version = version,
                exec_constraints = exec_constraints_formatted,
                target_constraints = target_constraints_formatted,
            )

        repository_ctx.file("BUILD.bazel", build_content)

        if is_mock:
            print("WARNING: Using mock {} implementation - real {} not found in PATH".format(tool_name, tool_name))

    return repository_rule(
        implementation = _impl,
        doc = "Creates a repository that contains a reference to the local {} installation or a mock implementation".format(tool_name),
    )
