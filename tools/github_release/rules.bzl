"""Bazel rule for fetching GitHub release assets for chezmoi."""

def _github_release_impl(ctx):
    output_file = ctx.actions.declare_file(ctx.label.name + ".toml")

    args = ctx.actions.args()
    args.add("--repo", ctx.attr.repo)
    args.add("--version", ctx.attr.version)
    args.add("--tool-name", ctx.attr.tool_name)
    args.add("--output", output_file.path)

    ctx.actions.run(
        outputs = [output_file],
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
        "_fetch_binary": attr.label(
            default = "//tools/github_release:fetch",
            executable = True,
            cfg = "exec",
        ),
    },
)

def github_release_update(name, repo, version):
    """
    Macro for creating targets to manage a GitHub release chezmoi data file.

    This creates two main targets:
    1. A `{name}_test` target that compares the generated file with the
       checked-in source file.
    2. A `{name}.update` target that prints the new file content to stdout.

    To update the file, run:
      bazel run //src:{name}.update > src/.chezmoiexternals/{name}.toml
    """
    generated_file_target = name + ".generated"
    source_file_label = "//src/.chezmoiexternals:" + name + ".toml"

    github_release(
        name = generated_file_target,
        tool_name = name,
        repo = repo,
        version = version,
    )

    native.py_test(
        name = name + "_test",
        srcs = ["//tools/github_release:fetch.py"],
        main = "//tools/github_release:fetch.py",
        args = [
            "--repo",
            repo,
            "--version",
            version,
            "--tool-name",
            name,
            "--output",
            "$(location " + source_file_label + ")",
            "--check",
        ],
        data = [source_file_label],
        deps = [
            "//tools/github_release:lib",
            "@pypi//aiohttp",
            "@pypi//click",
            "@pypi//toml",
        ],
    )

    native.py_binary(
        name = name + ".update",
        srcs = ["//tools/github_release:fetch.py"],
        main = "//tools/github_release:fetch.py",
        args = [
            "--repo",
            repo,
            "--version",
            version,
            "--tool-name",
            name,
            "--output",
            "-",
        ],
        deps = [
            "//tools/github_release:lib",
            "@pypi//aiohttp",
            "@pypi//click",
            "@pypi//toml",
        ],
    )