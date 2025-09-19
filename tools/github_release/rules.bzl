"""Bazel rule for fetching GitHub release assets for chezmoi."""

def _github_release_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".toml")

    args = ctx.actions.args()
    args.add("--repo", ctx.attr.repo)
    args.add("--version", ctx.attr.version)
    args.add("--tool-name", ctx.attr.tool_name)
    args.add("--asset-glob", ctx.attr.asset_glob)
    args.add("--output", output_file.path)

    ctx.actions.run(
        outputs = [output_file],
        inputs = [],
        executable = ctx.executable._fetch_binary,
        arguments = [args],
        mnemonic = "FetchGitHubRelease",
        progress_message = "Fetching release info for " + ctx.attr.tool_name,
    )

    return [DefaultInfo(files = depset([output_file]))]

github_release = rule(
    implementation = _github_release_impl,
    attrs = {
        "tool_name": attr.string(mandatory = True),
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

def github_release_update(name, repo, version, asset_glob):
    """
    Macro for creating targets to manage a GitHub release chezmoi data file.

    This creates two main targets:
    1. A `{name}_test` target that compares the generated file with the
       checked-in source file.
    2. A `{name}_update` target that prints the new file content to stdout.

    To update the file, run:
      bazel run //src:{name}_update > src/.chezmoidata/{name}.toml
    """
    generated_file_target = name + "_generated"
    source_file_label = ".chezmoidata/" + name + ".toml"

    github_release(
        name = generated_file_target,
        tool_name = name,
        repo = repo,
        version = version,
        asset_glob = asset_glob,
    )

    native.sh_test(
        name = name + "_test",
        srcs = ["//tools/github_release:diff_test.sh"],
        args = [
            "$(location :" + generated_file_target + ")",
            "$(location :" + source_file_label + ")",
        ],
        data = [
            ":" + generated_file_target,
            ":" + source_file_label,
        ],
    )

    native.sh_binary(
        name = name + "_update",
        srcs = ["//tools/github_release:update.sh"],
        args = ["$(location :" + generated_file_target + ")"],
        data = [":" + generated_file_target],
    )
