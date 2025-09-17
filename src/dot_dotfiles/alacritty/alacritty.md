# Alacritty

Alacritty is a cross-platform, GPU-accelerated terminal emulator focused on performance and simplicity.

## Official Documentation

- [Alacritty GitHub](https://github.com/alacritty/alacritty)
- [Configuration Guide](https://github.com/alacritty/alacritty/blob/master/alacritty.yml)
- [Installation Instructions](https://github.com/alacritty/alacritty/blob/master/INSTALL.md)

## Configuration Files

### Config File Locations
Alacritty searches for configuration files in this order:
1. `$XDG_CONFIG_HOME/alacritty/alacritty.yml`
2. `$XDG_CONFIG_HOME/alacritty.yml`
3. `$HOME/.config/alacritty/alacritty.yml`
4. `$HOME/.alacritty.yml`

### Platform-Specific Paths
- **macOS**: `~/.config/alacritty/alacritty.yml`
- **Linux**: `~/.config/alacritty/alacritty.yml`
- **Windows**: `%APPDATA%\alacritty\alacritty.yml`

## Configuration Structure

### Basic YAML Format
```yaml
# Window configuration
window:
  dimensions:
    columns: 120
    lines: 40

# Font configuration  
font:
  normal:
    family: "JetBrains Mono"
  size: 14.0

# Colors (example: Dracula theme)
colors:
  primary:
    background: '#282a36'
    foreground: '#f8f8f2'
```

### Cross-Platform Configuration
Use conditional blocks for platform-specific settings:
```yaml
# macOS specific
font:
  normal:
    family: "SF Mono"

# Alternative for Linux
# font:
#   normal:
#     family: "DejaVu Sans Mono"
```

## Key Features

### GPU Acceleration
Hardware-accelerated rendering for improved performance:
- Utilizes OpenGL for fast text rendering
- Efficient scrolling and screen updates
- Low input latency

### Font Configuration
Advanced font rendering with ligature support:
- Font family, size, and offset configuration
- Bold, italic, and bold-italic variants
- Glyph offset fine-tuning
- Built-in font fallback system

### Key Bindings
Custom keyboard shortcuts:
```yaml
key_bindings:
  - { key: V, mods: Command, action: Paste }
  - { key: C, mods: Command, action: Copy }
  - { key: N, mods: Command, action: SpawnNewInstance }
  - { key: Q, mods: Command, action: Quit }
```

### Color Schemes
Extensive theming support:
- 256-color and true color support
- Named color definitions
- Background opacity/transparency
- Cursor and selection colors

## Advanced Configuration

### Environment Variables
Set shell environment variables:
```yaml
env:
  TERM: alacritty
  WINIT_X11_SCALE_FACTOR: "1.0"
```

### Shell Configuration
Specify shell and startup commands:
```yaml
shell:
  program: /bin/zsh
  args:
    - --login
```

### Mouse and Cursor
Mouse behavior and cursor appearance:
```yaml
mouse:
  double_click: { threshold: 300 }
  triple_click: { threshold: 300 }

cursor:
  style: Block
  vi_mode_style: Underline
  blinking: Never
```

## Integration Patterns

### With chezmoi
```yaml
# Template for dynamic configuration
{{- if eq .chezmoi.os "darwin" }}
font:
  normal:
    family: "SF Mono"
{{- else if eq .chezmoi.os "linux" }}
font:
  normal:
    family: "DejaVu Sans Mono"  
{{- end }}
```

### Common Configurations
- **Font**: JetBrains Mono, Fira Code, SF Mono (macOS)
- **Theme**: Dracula, Solarized Dark, One Dark
- **Size**: 12-14pt for standard displays, 16-18pt for HiDPI
- **Opacity**: 0.9-0.95 for subtle transparency

### Performance Tuning
```yaml
# Optimize for performance
scrolling:
  history: 10000
  multiplier: 3

# Reduce input latency  
mouse:
  hide_when_typing: true

# Disable visual bell
bell:
  animation: EaseOutExpo
  duration: 0
```

## Troubleshooting

### Font Issues
- Ensure fonts are installed system-wide
- Use `fc-list` (Linux) or Font Book (macOS) to verify font names
- Test font rendering with `alacritty --print-events`

### Color Problems
- Verify TERM environment variable is set correctly
- Test with `alacritty --print-events` for debugging
- Check shell configuration for conflicting color settings