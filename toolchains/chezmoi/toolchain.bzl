"""
Toolchain rules for chezmoi.
"""

ChezmoimInfo = provider(
    doc = "Information about how to invoke the chezmoi executable.",
    fields = {
        "chezmoi_path": "Path to the chezmoi executable",
        "chezmoi_version": "Version of chezmoi being used",
        "env": "Environment variables to set when invoking chezmoi",
    },
)

def _chezmoi_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        chezmoiinfo = ChezmoimInfo(
            chezmoi_path = ctx.file.chezmoi_path,
            chezmoi_version = ctx.attr.chezmoi_version,
            env = ctx.attr.env,
        ),
    )
    return [toolchain_info]

chezmoi_toolchain = rule(
    implementation = _chezmoi_toolchain_impl,
    attrs = {
        "chezmoi_path": attr.label(
            doc = "Path to the chezmoi executable",
            allow_single_file = True,
            mandatory = True,
        ),
        "chezmoi_version": attr.string(
            doc = "Version of chezmoi being used",
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when invoking chezmoi",
            default = {},
        ),
    },
)
