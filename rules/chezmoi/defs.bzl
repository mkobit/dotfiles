"""Chezmoi build rules for Bazel."""

def _chezmoi_test_impl(ctx):
    """Test that chezmoi toolchain works by running chezmoi --version."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Create output file for version
    version_output = ctx.actions.declare_file("%s_version_output.txt" % ctx.label.name)

    # Create temp home directory
    temp_home = ctx.actions.declare_directory("%s_temp_home" % ctx.label.name)
    ctx.actions.run_shell(
        outputs = [temp_home],
        command = "mkdir -p %s" % temp_home.path,
        mnemonic = "CreateTempHome",
    )

    # Run chezmoi --version using run_shell to capture output
    ctx.actions.run_shell(
        inputs = [chezmoi_info.chezmoi_path, temp_home],
        outputs = [version_output],
        command = "HOME={} {} --version > {}".format(
            temp_home.path,
            chezmoi_info.chezmoi_path.path,
            version_output.path,
        ),
        mnemonic = "ChezmoiVersionTest",
        progress_message = "Testing chezmoi toolchain",
    )

    # Create a simple test wrapper that just succeeds if the version file exists
    test_executable = ctx.actions.declare_file("%s_test" % ctx.label.name)
    ctx.actions.write(
        output = test_executable,
        content = """#!/bin/bash
set -e
echo "Chezmoi toolchain test:"
cat "{version_file}"
echo "Chezmoi toolchain test passed!"
""".format(version_file = version_output.short_path),
        is_executable = True,
    )

    return [DefaultInfo(
        executable = test_executable,
        runfiles = ctx.runfiles(files = [version_output]),
    )]

chezmoi_test = rule(
    implementation = _chezmoi_test_impl,
    test = True,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)

def _chezmoi_version_impl(ctx):
    """Extract version from chezmoi binary."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Create temp home directory
    temp_home = ctx.actions.declare_directory("%s_temp_home" % ctx.label.name)
    ctx.actions.run_shell(
        outputs = [temp_home],
        command = "mkdir -p %s" % temp_home.path,
        mnemonic = "CreateTempHome",
    )

    # Extract version to file using ctx.actions.run
    version_file = ctx.actions.declare_file("%s_version.txt" % ctx.label.name)

    ctx.actions.run_shell(
        inputs = [chezmoi_info.chezmoi_path, temp_home],
        outputs = [version_file],
        command = "HOME={} {} --version > {}".format(
            temp_home.path,
            chezmoi_info.chezmoi_path.path,
            version_file.path,
        ),
        mnemonic = "ChezmoiVersion",
    )

    return [DefaultInfo(files = depset([version_file]))]

chezmoi_version = rule(
    implementation = _chezmoi_version_impl,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)
