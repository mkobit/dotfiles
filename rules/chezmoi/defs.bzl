"""Chezmoi build rules for Bazel."""

def _chezmoi_binary_impl(ctx):
    """Access the chezmoi binary from the toolchain."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    return [DefaultInfo(
        files = depset([chezmoi_info.chezmoi_path]),
    )]

chezmoi_binary = rule(
    implementation = _chezmoi_binary_impl,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)
