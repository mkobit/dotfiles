# Toolchain type definitions

# Provider for external tool information
ToolInfo = provider(
    doc = "Information about an external tool",
    fields = {
        "name": "Name of the tool",
        "path": "Path to the tool executable",
        "version": "Version string of the tool",
        "available": "Boolean indicating if the tool is available",
        "extra_info": "Dictionary of additional tool-specific information",
    },
)

def _tool_info_impl(ctx):
    return [
        ToolInfo(
            name = ctx.attr.tool_name,
            path = ctx.attr.path,
            version = ctx.attr.version,
            available = ctx.attr.available,
            extra_info = ctx.attr.extra_info,
        ),
        platform_common.ToolchainInfo(
            tool_info = ToolInfo(
                name = ctx.attr.tool_name,
                path = ctx.attr.path,
                version = ctx.attr.version,
                available = ctx.attr.available,
                extra_info = ctx.attr.extra_info,
            ),
        ),
    ]

tool_info = rule(
    implementation = _tool_info_impl,
    attrs = {
        "tool_name": attr.string(mandatory = True),
        "path": attr.string(mandatory = True),
        "version": attr.string(default = ""),
        "available": attr.bool(default = True),
        "extra_info": attr.string_dict(default = {}),
    },
)