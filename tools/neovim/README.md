# Neovim Configuration

This directory contains the implementation for the Neovim configuration system. The configurations here work in conjunction with the rule definitions in `modules/neovim`.

## Directory Structure

```
tools/neovim/
├── BUILD.bazel          # Build rules for Neovim configuration
├── configs/             # Configuration files
│   ├── generic.lua      # Generic platform Lua settings
│   ├── generic.vim      # Generic platform VimL settings  
│   ├── linux_specific.lua  # Linux-specific Lua settings
│   ├── linux_specific.vim  # Linux-specific VimL settings
│   ├── macos_specific.lua  # macOS-specific Lua settings
│   ├── macos_specific.vim  # macOS-specific VimL settings
│   ├── neovim_base.vim  # Base Neovim VimL configuration
│   ├── neovim_lua.lua   # Base Neovim Lua configuration
│   ├── personal_variant.vim # Personal variant settings
│   ├── windows_specific.lua # Windows-specific Lua settings
│   ├── windows_specific.vim # Windows-specific VimL settings
│   ├── work_variant.vim     # Work variant settings
│   ├── wsl_specific.lua     # WSL-specific Lua settings
│   └── wsl_specific.vim     # WSL-specific VimL settings
└── README.md            # This file
```

## Features

- Dual VimL/Lua configuration system
- Platform-specific settings
- Variant-specific settings (work, personal)
- Modern Lua-based plugin system
- Sensible defaults for all environments

## Usage

### Building Configurations

```bash
# Generate basic Neovim configuration
bazel build //tools/neovim:neovim_conf_generated

# Generate platform-specific configuration
bazel build //tools/neovim:neovim_conf_combined

# Generate unified configuration (platform + feature detection)
bazel build //tools/neovim:neovim_conf_unified
```

### Installing Configurations

```bash
# Install basic dotfiles
bazel run //tools/neovim:neovim_dotfiles

# Install unified configuration
bazel run //tools/neovim:neovim_unified_dotfiles
```

### Testing Configurations

```bash
# Check Neovim version and feature support
bazel run //tools/neovim:show_neovim_version

# Validate configuration files
bazel run //tools/neovim:validate_neovim_config
```

## Plugin Management

The configuration uses [lazy.nvim](https://github.com/folke/lazy.nvim) for plugin management. Plugins are defined in the Lua configuration files.

## Troubleshooting

If you encounter issues with the Neovim configuration:

1. Check Neovim version: `nvim --version`
2. Validate the configuration: `bazel run //tools/neovim:validate_neovim_config`
3. Try the basic configuration: `bazel run //tools/neovim:neovim_dotfiles`
4. Check logs: `cat ~/.local/share/nvim/log`