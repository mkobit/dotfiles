# Ghostty

Ghostty is a fast, feature-rich terminal emulator that is GPU-accelerated, cross-platform, and supports various advanced terminal features.

## Official Documentation

- [Ghostty Official Site](https://ghostty.org/)
- [Installation Guide](https://ghostty.org/docs/install/binary)
- [Configuration Documentation](https://ghostty.org/docs/config/reference)
- [GitHub Repository](https://github.com/ghostty-org/ghostty)

## Installation

### Automated Installation (via chezmoi)
Ghostty is installed automatically via package managers when `ghostty.installation = "package-manager"` is set in `.chezmoidata.toml`.

**Supported platforms:**
- **macOS**: Homebrew Cask (`brew install --cask ghostty`)
- **Ubuntu/Debian**: apt package manager
- **Arch Linux**: pacman (official repositories)
- **Fedora**: dnf package manager

### Manual Installation
For unsupported distributions, see the [official installation guide](https://ghostty.org/docs/install/binary).

### Uninstallation
Set `ghostty.installation = "disabled"` in `.chezmoidata.toml` to automatically uninstall Ghostty and clean up configuration files.

## Configuration Files

### Config File Location
Ghostty searches for configuration files in this order:
1. `$XDG_CONFIG_HOME/ghostty/config`
2. `$HOME/.config/ghostty/config`
3. `$HOME/.ghostty`

### Platform-Specific Paths
- **macOS**: `~/.config/ghostty/config`
- **Linux**: `~/.config/ghostty/config`
- **Windows**: `%APPDATA%\ghostty\config`

## Configuration Structure

### Basic Configuration Format
Ghostty uses a simple key-value configuration format:
```
# Window configuration
window-width = 120
window-height = 40

# Font configuration
font-size = 14
font-family = "JetBrains Mono"

# Theme
theme = "dracula"
```

### Cross-Platform Configuration
Ghostty uses a single config file; manage platform differences via chezmoi templates:
```
# Platform-specific font via chezmoi templating
{{- if eq .chezmoi.os "darwin" }}
font-family = "SF Mono"
{{- else }}
font-family = "DejaVu Sans Mono"
{{- end }}
```

## Key Features

### GPU Acceleration
Hardware-accelerated rendering for improved performance:
- Metal rendering on macOS
- OpenGL rendering on Linux
- Efficient text rendering and scrolling
- Low input latency

### Advanced Terminal Features
Modern terminal capabilities:
- True color support (24-bit)
- Unicode support including emoji
- Ligatures and advanced font rendering
- Hyperlinks and OSC sequences
- Synchronized output
- Bracketed paste mode

### Font Configuration
Advanced typography support:
```
font-family = "JetBrains Mono"
font-size = 14
font-weight = normal
font-style = normal

# Enable font ligatures
font-feature = "liga"
font-feature = "calt"
```

### Key Bindings
Custom keyboard shortcuts:
```
# Copy/Paste
keybind = cmd+c=copy_to_clipboard
keybind = cmd+v=paste_from_clipboard

# Window management
keybind = cmd+n=new_window
keybind = cmd+t=new_tab

# Font size adjustment
keybind = cmd+plus=increase_font_size:1
keybind = cmd+minus=decrease_font_size:1
```

### Themes and Colors
Built-in theme support:
```
# Use built-in themes
theme = "dracula"
theme = "solarized-dark"
theme = "catppuccin-mocha"

# Or define custom colors
background = 282a36
foreground = f8f8f2
cursor-color = f8f8f2

# ANSI colors
palette = 0=#21222c
palette = 1=#ff5555
palette = 2=#50fa7b
```

## Advanced Configuration

### Shell Configuration
Specify shell and startup behavior:
```
shell-integration = zsh
shell-integration-features = cursor,sudo,title
command = /bin/zsh
```

### Window Behavior
Window appearance and behavior:
```
window-decoration = true
window-title-font-family = "SF Pro Display"
window-save-state = default
window-new-tab-position = after
```

### Mouse and Cursor
Mouse behavior and cursor appearance:
```
mouse-hide-while-typing = true
cursor-style = block
cursor-style-blink = false
cursor-text = background
```

### Performance Tuning
```
# Optimize for performance
scrollback-limit = 100000
minimum-contrast = 1.0

# Reduce visual effects for better performance
window-vsync = false
```

## Integration Patterns

### With chezmoi
```
# Template for dynamic configuration
{{- if eq .chezmoi.os "darwin" }}
font-family = "SF Mono"
font-size = 14
{{- else if eq .chezmoi.os "linux" }}
font-family = "DejaVu Sans Mono"
font-size = 12
{{- end }}

# Profile-specific settings
{{- if .git.personal.enabled }}
window-title = "Ghostty - Personal"
{{- else }}
window-title = "Ghostty - Work"
{{- end }}
```

### Common Configurations
- **Font**: JetBrains Mono, Fira Code, SF Mono (macOS), Cascadia Code
- **Theme**: Dracula, Catppuccin, Solarized Dark, One Dark Pro
- **Size**: 12-14pt for standard displays, 16-18pt for HiDPI
- **Performance**: Disable vsync for lower latency, increase scrollback for history

### Shell Integration
```
# Enable shell integration for enhanced features
shell-integration = zsh
shell-integration-features = cursor,sudo,title,jump

# Configure prompt integration
shell-integration-cursor = true
```

## Troubleshooting

### Font Issues
- Ensure fonts are installed system-wide
- Use `fc-list` (Linux) or Font Book (macOS) to verify font names
- Check font file permissions and accessibility

### Performance Issues
- Disable window composition effects
- Reduce scrollback limit
- Disable unnecessary visual features
- Check GPU driver compatibility

### Color Problems
- Verify terminal color support with `ghostty --print-config`
- Test color output with standard tools
- Check shell configuration for conflicting settings

### Installation Issues
- **macOS**: Ensure Homebrew is installed and updated
- **Linux**: Verify package manager access and update repositories
- **All**: Check system requirements and compatibility

## Configuration Migration

### From Other Terminals
Ghostty provides migration tools and compatibility modes for:
- iTerm2 color schemes
- Alacritty configuration
- Terminal.app settings

### Backup Configuration
```bash
# Backup current configuration
cp ~/.config/ghostty/config ~/.config/ghostty/config.backup

# Restore from backup
cp ~/.config/ghostty/config.backup ~/.config/ghostty/config
```