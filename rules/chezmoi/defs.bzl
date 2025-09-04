"""Chezmoi build rules for Bazel."""

def _chezmoi_test_impl(ctx):
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Create a simple test script that runs chezmoi --version
    test_script = ctx.actions.declare_file("%s_test.sh" % ctx.label.name)

    # Use provided home directory or default to /tmp
    home_dir = ctx.attr.home if ctx.attr.home else "/tmp"

    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -e
echo "Testing chezmoi toolchain..."
# Set required environment variables for chezmoi
export HOME={home_dir}
# Use runfiles path for hermetic execution  
CHEZMOI_PATH="$0.runfiles/_main/{chezmoi_path}"
if [[ -f "$CHEZMOI_PATH" ]]; then
    "$CHEZMOI_PATH" --version
else
    # Fallback to direct path
    {chezmoi_path} --version
fi
echo "Chezmoi toolchain test passed!"
""".format(chezmoi_path = chezmoi_info.chezmoi_path.short_path, home_dir = home_dir),
        is_executable = True,
    )

    return [DefaultInfo(
        executable = test_script,
        runfiles = ctx.runfiles(files = [chezmoi_info.chezmoi_path]),
    )]

chezmoi_test = rule(
    implementation = _chezmoi_test_impl,
    attrs = {
        "home": attr.string(
            doc = "HOME directory to use during chezmoi operations",
            default = "/tmp",
        ),
    },
    test = True,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)

def _chezmoi_source_tree_impl(ctx):
    """Generate a chezmoi source tree from input files."""
    chezmoi_toolchain = ctx.toolchains["//toolchains/chezmoi:toolchain_type"]
    chezmoi_info = chezmoi_toolchain.chezmoiinfo

    # Create output directory
    source_tree = ctx.actions.declare_directory(ctx.label.name)

    # Collect all input files
    input_files = []
    for src in ctx.attr.srcs:
        input_files.extend(src.files.to_list())

    # Profile data file
    profile_data_file = None
    if ctx.file.profile_data:
        profile_data_file = ctx.file.profile_data
        input_files.append(profile_data_file)

    # Create script to generate source tree
    script = ctx.actions.declare_file("%s_generate.sh" % ctx.label.name)

    # Use provided home directory or default to /tmp
    home_dir = ctx.attr.home if ctx.attr.home else "/tmp"

    script_content = """#!/bin/bash
set -e
export HOME={home_dir}

# Create source tree directory
mkdir -p {output_dir}

# Copy source files to output directory
""".format(output_dir = source_tree.path, home_dir = home_dir)

    # Add commands to copy source files
    for src_file in input_files:
        if src_file.is_directory:
            script_content += 'cp -r "{}" "{}/"\n'.format(src_file.path, source_tree.path)
        else:
            script_content += 'cp "{}" "{}/"\n'.format(src_file.path, source_tree.path)

    # Add profile data handling
    if profile_data_file:
        script_content += '''
# Copy profile data to .chezmoidata/
mkdir -p {output_dir}/.chezmoidata
cp "{profile_data}" "{output_dir}/.chezmoidata/config.yaml"
'''.format(output_dir = source_tree.path, profile_data = profile_data_file.path)

    ctx.actions.write(
        output = script,
        content = script_content,
        is_executable = True,
    )

    # Run the generation script
    ctx.actions.run(
        inputs = input_files + [chezmoi_info.chezmoi_path],
        outputs = [source_tree],
        executable = script,
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
        "home": attr.string(
            doc = "HOME directory to use during chezmoi operations",
            default = "/tmp",
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

    # Create validation script
    validation_script = ctx.actions.declare_file("%s_validate.sh" % ctx.label.name)

    # Use provided home directory or default to /tmp
    home_dir = ctx.attr.home if ctx.attr.home else "/tmp"

    ctx.actions.write(
        output = validation_script,
        content = """#!/bin/bash
set -e
export HOME={home_dir}

echo "Validating chezmoi source tree..."
cd "{source_tree}"

# Run chezmoi apply --dry-run for validation
{chezmoi_path} apply --dry-run

echo "Chezmoi validation passed!"
""".format(
            source_tree = source_tree.path,
            chezmoi_path = chezmoi_info.chezmoi_path.path,
            home_dir = home_dir,
        ),
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
        "home": attr.string(
            doc = "HOME directory to use during chezmoi operations",
            default = "/tmp",
        ),
    },
    test = True,
    toolchains = ["//toolchains/chezmoi:toolchain_type"],
)
