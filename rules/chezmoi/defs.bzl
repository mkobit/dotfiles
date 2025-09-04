"""Chezmoi build rules for Bazel."""

def _chezmoi_test_impl(ctx):
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Simple test script - use mktemp for HOME since we just need chezmoi to run
    test_script = ctx.actions.declare_file("%s_test.sh" % ctx.label.name)

    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -e
echo "Testing chezmoi toolchain..."
export HOME=$(mktemp -d)
trap "rm -rf $HOME" EXIT
# Use runfiles path for chezmoi binary
CHEZMOI_PATH="$0.runfiles/_main/{chezmoi_path}"
if [[ -f "$CHEZMOI_PATH" ]]; then
    "$CHEZMOI_PATH" --version
else
    {chezmoi_path} --version
fi
echo "Chezmoi toolchain test passed!"
""".format(chezmoi_path = chezmoi_info.chezmoi_path.short_path),
        is_executable = True,
    )

    return [DefaultInfo(
        executable = test_script,
        runfiles = ctx.runfiles(files = [chezmoi_info.chezmoi_path]),
    )]

chezmoi_test = rule(
    implementation = _chezmoi_test_impl,
    test = True,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)

def _chezmoi_source_tree_impl(ctx):
    """Generate a chezmoi source tree from input files."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Output directory - Bazel creates this automatically
    source_tree = ctx.actions.declare_directory(ctx.label.name)

    # Collect all input files
    input_files = []
    for src in ctx.attr.srcs:
        input_files.extend(src.files.to_list())

    # Profile data file
    if ctx.file.profile_data:
        input_files.append(ctx.file.profile_data)

    # Generate source tree using run_shell for simplicity
    args = []
    for src_file in ctx.attr.srcs:
        for f in src_file.files.to_list():
            if f.is_directory:
                args.append("cp -r {} {}/".format(f.path, source_tree.path))
            else:
                args.append("cp {} {}/".format(f.path, source_tree.path))

    if ctx.file.profile_data:
        args.extend([
            "mkdir -p {}/.chezmoidata".format(source_tree.path),
            "cp {} {}/.chezmoidata/config.yaml".format(ctx.file.profile_data.path, source_tree.path),
        ])

    ctx.actions.run_shell(
        inputs = input_files,
        outputs = [source_tree],
        command = " && ".join(args),
        mnemonic = "ChezmoiSourceTree",
        progress_message = "Generating chezmoi source tree %s" % ctx.label.name,
    )

    return [DefaultInfo(files = depset([source_tree]))]

chezmoi_source_tree = rule(
    implementation = _chezmoi_source_tree_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Source files to include in the chezmoi source tree",
            allow_files = True,
            mandatory = True,
        ),
        "profile_data": attr.label(
            doc = "Profile data file (will be copied to .chezmoidata/config.yaml)",
            allow_single_file = True,
        ),
    },
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)

def _chezmoi_validate_impl(ctx):
    """Run chezmoi apply --dry-run for validation."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Get source tree
    source_tree = ctx.attr.source_tree.files.to_list()[0]

    # Simple validation script
    validation_script = ctx.actions.declare_file("%s_validate.sh" % ctx.label.name)

    ctx.actions.write(
        output = validation_script,
        content = """#!/bin/bash
set -e
echo "Validating chezmoi source tree..."
export HOME=$(mktemp -d) 
trap "rm -rf $HOME" EXIT
cd "$1"
"$2" apply --dry-run
echo "Chezmoi validation passed!"
""",
        is_executable = True,
    )

    return [DefaultInfo(
        executable = validation_script,
        runfiles = ctx.runfiles(files = [source_tree, chezmoi_info.chezmoi_path]),
    )]

chezmoi_validate_test = rule(
    implementation = _chezmoi_validate_impl,
    attrs = {
        "source_tree": attr.label(
            doc = "Chezmoi source tree to validate",
            mandatory = True,
        ),
    },
    test = True,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)
