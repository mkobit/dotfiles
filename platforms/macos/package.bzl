"""macOS-specific package configurations."""

# Default packages for macOS
MACOS_DEFAULT_PACKAGES = [
    "git",
    "curl",
    "wget",
    "htop",
    "tmux",
    "neovim",
    "ripgrep",
    "fd",
    "fzf",
    "jq",
    "bat",
    "exa",
]

# Default casks for macOS
MACOS_DEFAULT_CASKS = [
    "iterm2",
    "rectangle",
    "alt-tab",
]

# Default taps for macOS
MACOS_DEFAULT_TAPS = [
    "homebrew/cask-fonts",
]

# Development packages for macOS
MACOS_DEV_PACKAGES = MACOS_DEFAULT_PACKAGES + [
    "python",
    "node",
    "go",
    "rustup-init",
    "cmake",
    "ninja",
    "bazel",
]

# Development casks for macOS
MACOS_DEV_CASKS = MACOS_DEFAULT_CASKS + [
    "visual-studio-code",
    "docker",
    "firefox",
]