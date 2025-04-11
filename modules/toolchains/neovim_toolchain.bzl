"""Toolchain for Neovim."""

# Neovim toolchain info
NeovimInfo = provider(
    doc = "Information about Neovim installation",
    fields = {
        "path": "Path to Neovim executable",
        "version": "Neovim version",
        "has_lua": "Whether Neovim has Lua support",
        "has_python": "Whether Neovim has Python support",
    },
)

def _neovim_toolchain_impl(ctx):
    """Implementation of neovim_toolchain rule."""
    nvim_info = platform_common.ToolchainInfo(
        neoviminfo = NeovimInfo(
            path = ctx.attr.path,
            version = ctx.attr.version,
            has_lua = ctx.attr.has_lua,
            has_python = ctx.attr.has_python,
        ),
        # Add config_path and runtime_path to match the existing calls
        config_path = ctx.attr.config_path,
        runtime_path = ctx.attr.runtime_path,
    )
    return [nvim_info]

neovim_toolchain = rule(
    implementation = _neovim_toolchain_impl,
    attrs = {
        "path": attr.string(
            doc = "Path to Neovim executable",
            default = "",
        ),
        "version": attr.string(
            doc = "Neovim version",
            default = "",
        ),
        "has_lua": attr.bool(
            doc = "Whether Neovim has Lua support",
            default = False,
        ),
        "has_python": attr.bool(
            doc = "Whether Neovim has Python support",
            default = False,
        ),
        "config_path": attr.string(
            doc = "Path to Neovim config directory",
            default = "~/.config/nvim",
        ),
        "runtime_path": attr.string(
            doc = "Path to Neovim runtime directory",
            default = "",
        ),
    },
)

def _neovim_toolchain_register_impl(ctx):
    """Implementation of neovim_toolchain_register rule."""
    # Try to detect Neovim information using a genrule
    output = ctx.actions.declare_file(ctx.label.name + "_toolchain_info")
    
    # Execute Neovim to get its version and features
    ctx.actions.run_shell(
        outputs = [output],
        command = """
        if command -v nvim &>/dev/null; then
            echo "detected=true" > {output}
            echo "path=$(which nvim)" >> {output}
            echo "version=$(nvim --version | head -1 | sed 's/.*NVIM v//;s/ .*//g')" >> {output}
            
            # Check for Lua support based on version
            version=$(nvim --version | head -1 | sed 's/.*NVIM v//;s/ .*//g')
            major_version=$(echo $version | cut -d. -f1)
            minor_version=$(echo $version | cut -d. -f2)
            
            if [[ "$major_version" -gt 0 || "$minor_version" -ge 5 ]]; then
                echo "has_lua=true" >> {output}
            else
                echo "has_lua=false" >> {output}
            fi
            
            # Check for Python support
            if nvim --version | grep -q '+python3'; then
                echo "has_python=true" >> {output}
            else
                echo "has_python=false" >> {output}
            fi
        else
            echo "detected=false" > {output}
            echo "path=" >> {output}
            echo "version=" >> {output}
            echo "has_lua=false" >> {output}
            echo "has_python=false" >> {output}
        fi
        """.format(output = output.path),
    )
    
    # Create the toolchain registration
    template = """
# Generated file - DO NOT EDIT
load("@//:BUILD.bazel", "neovim_toolchain_type")
load("//modules/toolchains:neovim_toolchain.bzl", "neovim_toolchain")

package(default_visibility = ["//visibility:public"])

# Neovim toolchain based on detected info
neovim_toolchain(
    name = "neovim_toolchain_impl",
    path = "{path}",
    version = "{version}",
    has_lua = {has_lua},
    has_python = {has_python},
)

# Toolchain registration
toolchain(
    name = "neovim_toolchain",
    exec_compatible_with = [
        {exec_constraints}
    ],
    target_compatible_with = [
        {target_constraints}
    ],
    toolchain = ":neovim_toolchain_impl",
    toolchain_type = "//:neovim_toolchain_type",
)
"""
    
    exec_constraints = ""
    target_constraints = ""
    
    if ctx.attr.exec_compatible_with:
        exec_constraints = ",\n        ".join(['"%s"' % c for c in ctx.attr.exec_compatible_with])
    
    if ctx.attr.target_compatible_with:
        target_constraints = ",\n        ".join(['"%s"' % c for c in ctx.attr.target_compatible_with])
    
    # Create the output build file
    ctx.actions.write(
        output = ctx.outputs.build_file,
        content = template.format(
            path = "${NVIM_PATH}",
            version = "${NVIM_VERSION}",
            has_lua = "${NVIM_HAS_LUA}",
            has_python = "${NVIM_HAS_PYTHON}",
            exec_constraints = exec_constraints,
            target_constraints = target_constraints,
        ),
    )
    
    # Create the output script
    script_content = """#!/bin/bash
# Read detected info
source {info_file}

# Process the template
sed -e "s|${{NVIM_PATH}}|$path|g" \\
    -e "s|${{NVIM_VERSION}}|$version|g" \\
    -e "s|${{NVIM_HAS_LUA}}|$has_lua|g" \\
    -e "s|${{NVIM_HAS_PYTHON}}|$has_python|g" \\
    {build_file_template} > {output}

# Make sure the directory exists
mkdir -p $(dirname {output})
""".format(
        info_file = output.path,
        build_file_template = ctx.outputs.build_file.path,
        output = ctx.attr.output_dir + "/BUILD.bazel",
    )
    
    ctx.actions.write(
        output = ctx.outputs.executable,
        content = script_content,
        is_executable = True,
    )
    
    return [DefaultInfo(
        files = depset([ctx.outputs.build_file, output]),
        runfiles = ctx.runfiles(files = [ctx.outputs.build_file, output]),
    )]

neovim_toolchain_register = rule(
    implementation = _neovim_toolchain_register_impl,
    attrs = {
        "output_dir": attr.string(
            doc = "Directory where the toolchain registration will be written",
            default = "toolchains/neovim",
        ),
        "_exec_constraints": attr.string_list(
            doc = "Constraints for execution platform",
            default = [],
        ),
        "_target_constraints": attr.string_list(
            doc = "Constraints for target platform",
            default = [],
        ),
    },
    outputs = {
        "build_file": "%{name}.BUILD",
    },
    executable = True,
)

def _neovim_test_impl(ctx):
    """Implementation for neovim_test."""
    output = ctx.actions.declare_file(ctx.label.name + ".sh")
    
    content = """#!/bin/bash
echo "Running Neovim system integration test"

if ! command -v nvim &>/dev/null; then
    echo "Neovim not found, test skipped"
    exit 0
fi

# Create a temporary configuration file
tmp_config=$(mktemp)
cat > $tmp_config << 'EOT'
set nocompatible
set runtimepath-=~/.config/nvim
set runtimepath-=~/.local/share/nvim/site
" Test basic functionality
let test_var = 123
if test_var == 123
  " Test passed
  let g:test_result = "pass"
else
  " Test failed
  let g:test_result = "fail"
endif

echo "Test result: " . g:test_result
quit
EOT

# Run Neovim with the test configuration
nvim -u $tmp_config --headless -c 'echo "Test completed successfully" | quit' 2>/dev/null
test_result=$?

# Clean up
rm -f $tmp_config

if [ $test_result -eq 0 ]; then
    echo "Neovim basic functionality test passed"
    exit 0
else
    echo "Neovim basic functionality test failed"
    exit 1
fi
"""
    
    ctx.actions.write(
        output = output,
        content = content,
        is_executable = True,
    )
    
    return [DefaultInfo(
        files = depset([output]),
        executable = output,
    )]

neovim_test = rule(
    implementation = _neovim_test_impl,
    test = True,
)