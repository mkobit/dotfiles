# iTerm

iTerm2 is a terminal emulator for macOS with advanced features and extensive customization options.

## Official Documentation

- [iTerm2 Documentation](https://iterm2.com/documentation.html)
- [Features Overview](https://iterm2.com/features.html)
- [Python API](https://iterm2.com/python-api/)

## Configuration Files

### Preferences Location
- `~/Library/Preferences/com.googlecode.iterm2.plist`
- Managed via iTerm2 > Preferences > General > Preferences > Load preferences from custom folder

### Dynamic Profiles
- `~/Library/Application Support/iTerm2/DynamicProfiles/`
- JSON format for programmatic profile management
- Supports templating and conditional loading

## Key Features

### Shell Integration
Enables enhanced features like command status, directory tracking, and badges.
- [Shell Integration Setup](https://iterm2.com/documentation-shell-integration.html)
- Download: `curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | bash`

### Python Scripting
Full automation via Python API for window management, text processing, and automation.
- [Python API Documentation](https://iterm2.com/python-api/index.html)
- [Tutorial](https://iterm2.com/python-api/tutorial/index.html)

### Key Bindings
Custom keyboard shortcuts and key mappings.
- Preferences > Keys > Key Bindings
- Supports sending text, executing commands, and invoking scripts

### Profiles
Terminal appearance, behavior, and command settings.
- Color schemes, fonts, window settings
- Startup commands and working directory
- Dynamic profile loading via JSON

## Integration Patterns

### With chezmoi
```bash
# Dynamic profile generation
{{- if eq .chezmoi.os "darwin" }}
# Generate iTerm2 profiles based on environment
{{- end }}
```

### Common Configurations
- Font: JetBrains Mono, Fira Code with ligatures
- Color schemes: Dracula, Solarized Dark, custom themes
- Key bindings: Cmd+K clear, Cmd+D split vertically
- Shell integration: Fish, Zsh with Oh My Zsh

### Automation Examples
- Badge display for current git branch
- Automatic directory-based profile switching
- Command status indicators and notifications

## Advanced Features

### Tmux Integration
- [tmux Integration Mode](https://iterm2.com/documentation-tmux-integration.html)
- Native tmux window/pane management
- `tmux -CC` for control mode

### Triggers
Text-based automation rules for highlighting, notifications, and actions.
- Regular expression matching
- Bounce dock icon, run command, highlight text
- Preferences > Profiles > Advanced > Triggers