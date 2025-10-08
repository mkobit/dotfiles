"""Bazel rule for fetching GitHub release assets for chezmoi."""

def _github_release_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".toml")

    args = ctx.actions.args()
    args.add("--repo", ctx.attr.repo)
    args.add("--version", ctx.attr.version)
    args.add("--dest", ctx.attr.dest)
    args.add("--asset-glob", ctx.attr.asset_glob)
    args.add("--output", output_file.path)

    ctx.actions.run(
        outputs = [output_file],
        executable = ctx.executable._fetch_binary,
        arguments = [args],
        mnemonic = "FetchGitHubRelease",
        progress_message = "Fetching release info for " + ctx.attr.dest,
    )

    return [DefaultInfo(files = depset([output_file]))]

github_release = rule(
    implementation = _github_release_impl,
    attrs = {
        "dest": attr.string(mandatory = True),
        "repo": attr.string(mandatory = True),
        "version": attr.string(mandatory = True),
        "asset_glob": attr.string(mandatory = True),
        "_fetch_binary": attr.label(
            default = "//tools/github_release:fetch",
            executable = True,
            cfg = "exec",
        ),
    },
)