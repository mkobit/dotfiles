"""
Hammerspoon configuration rules for dotfiles.
"""

load("@bazel_skylib//lib:paths.bzl", "paths")

HammerspoonInfo = provider(
    doc = "Provider for Hammerspoon configuration data.",
    fields = {
        "configs": "Dict mapping config file paths to their contents",
        "init_lua": "The main Hammerspoon init.lua file content",
        "modules": "Dict mapping module names to their lua implementations",
    },
)

def _hammerspoon_config_impl(ctx):
    """Implementation of hammerspoon_config rule."""
    configs = {}
    modules = {}
    
    for src in ctx.files.srcs:
        path = src.short_path
        if path.startswith("../"):
            path = path[3:]
        configs[path] = src

    for module in ctx.files.modules:
        path = module.short_path
        if path.startswith("../"):
            path = path[3:]
        modules[paths.basename(path)] = module

    init_lua = ctx.file.init_lua

    return [
        HammerspoonInfo(
            configs = configs,
            init_lua = init_lua,
            modules = modules,
        ),
        DefaultInfo(files = depset([init_lua] + ctx.files.srcs + ctx.files.modules)),
    ]

hammerspoon_config = rule(
    implementation = _hammerspoon_config_impl,
    doc = "Rule for defining a Hammerspoon configuration",
    attrs = {
        "init_lua": attr.label(
            doc = "Main init.lua file for Hammerspoon",
            allow_single_file = True,
            mandatory = True,
        ),
        "srcs": attr.label_list(
            doc = "Configuration files for Hammerspoon",
            allow_files = True,
            default = [],
        ),
        "modules": attr.label_list(
            doc = "Lua modules for Hammerspoon",
            allow_files = [".lua"],
            default = [],
        ),
    },
)

def _hammerspoon_install_impl(ctx):
    """Implementation of hammerspoon_install rule."""
    config = ctx.attr.config[HammerspoonInfo]
    output_dir = ctx.actions.declare_directory(ctx.label.name)
    
    install_script = ctx.actions.declare_file(ctx.label.name + "_install.sh")
    
    script_content = """#!/bin/bash
set -eu

DEST_DIR="{dest_dir}"
SOURCE_DIR="{source_dir}"

mkdir -p "$DEST_DIR"

# Copy init.lua
cp "{init_lua}" "$DEST_DIR/init.lua"

# Copy all config files
""".format(
        dest_dir = ctx.attr.install_dir,
        source_dir = output_dir.path,
        init_lua = config.init_lua.path,
    )
    
    for path, src in config.configs.items():
        if path.endswith(".lua"):
            script_content += 'mkdir -p "$(dirname "$DEST_DIR/{path}")" && cp "{src}" "$DEST_DIR/{path}"\n'.format(
                path = path,
                src = src.path,
            )
    
    # Create modules directory and copy modules
    script_content += '\n# Copy all modules\nmkdir -p "$DEST_DIR/modules"\n'
    
    for name, src in config.modules.items():
        script_content += 'cp "{src}" "$DEST_DIR/modules/{name}"\n'.format(
            name = name,
            src = src.path,
        )
    
    ctx.actions.write(install_script, script_content, is_executable = True)
    
    print_paths_script = ctx.actions.declare_file(ctx.label.name + "_print_paths.sh")
    ctx.actions.write(
        print_paths_script,
        "#!/bin/bash\necho \"Hammerspoon config will be installed to: {}\"\n".format(ctx.attr.install_dir),
        is_executable = True,
    )
    
    return [
        DefaultInfo(
            executable = install_script,
            files = depset([install_script, print_paths_script, output_dir]),
        ),
    ]

hammerspoon_install = rule(
    implementation = _hammerspoon_install_impl,
    doc = "Rule for installing Hammerspoon configuration",
    attrs = {
        "config": attr.label(
            doc = "The Hammerspoon configuration to install",
            providers = [HammerspoonInfo],
            mandatory = True,
        ),
        "install_dir": attr.string(
            doc = "Directory where to install the Hammerspoon configuration",
            default = "$HOME/.hammerspoon",
        ),
    },
    executable = True,
)