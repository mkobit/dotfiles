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

def _extract_chezmoi_version_impl(ctx):
    """Extract version from chezmoi binary."""
    chezmoi_binary = ctx.file.chezmoi_binary
    version_file = ctx.actions.declare_file("chezmoi_version.txt")

    # Create temp home directory
    temp_home = ctx.actions.declare_directory("temp_home")
    ctx.actions.run_shell(
        outputs = [temp_home],
        command = "mkdir -p %s" % temp_home.path,
        mnemonic = "CreateTempHome",
    )

    # Extract version using shell to parse the output
    ctx.actions.run_shell(
        inputs = [chezmoi_binary, temp_home],
        outputs = [version_file],
        command = """
HOME={} {} --version | head -1 | awk '{{print $3}}' | sed 's/^v//' > {}
""".format(temp_home.path, chezmoi_binary.path, version_file.path),
        mnemonic = "ExtractChezmoiVersion",
    )

    return [DefaultInfo(files = depset([version_file]))]

_extract_chezmoi_version = rule(
    implementation = _extract_chezmoi_version_impl,
    attrs = {
        "chezmoi_binary": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
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
