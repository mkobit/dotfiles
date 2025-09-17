# Rectangle Pro

Rectangle Pro is a window management utility for macOS with advanced features for organizing windows and multi-monitor setups.

## Official Documentation

- [Rectangle Pro Website](https://rectangleapp.com/pro)
- [Rectangle GitHub](https://github.com/rxhanson/Rectangle) (open source version)
- [Keyboard Shortcuts Reference](https://rectangleapp.com/pro/keyboard-shortcuts)

## Configuration Files

### Preferences Location
- `~/Library/Preferences/com.knollsoft.Rectangle.plist`
- Managed via Rectangle Pro > Preferences

### Configuration Export/Import
Rectangle Pro allows exporting and importing configurations as JSON files.
- Rectangle Pro > Preferences > Export/Import
- Useful for syncing settings across machines

## Key Features

### Window Snapping
- Left/Right Half: `Ctrl+Option+←/→`
- Maximize: `Ctrl+Option+Enter`
- Center: `Ctrl+Option+C`
- Quarters: `Ctrl+Option+U/I/J/K`

### Multi-Monitor Support
- Move between displays
- Display-specific window layouts
- Monitor-aware snapping and resizing

### Custom Shortcuts
Configurable keyboard shortcuts for any window action.
- Preferences > Shortcuts
- Supports modifier key combinations
- Can disable conflicting shortcuts

### Advanced Layouts
Pro features include:
- Custom window layouts and saved positions
- Percentage-based sizing (33%, 66%, etc.)
- Window history and restoration
- Floating windows and ignore lists

## Configuration Management

### CLI Integration
Rectangle Pro supports command-line control for automation:
```bash
# Example: Move window to left half
osascript -e 'tell application "Rectangle Pro" to move window to left half'
```

### Automation Scripts
AppleScript integration for complex window management workflows:
```applescript
tell application "Rectangle Pro"
    move window 1 to left half
    move window 2 to right half
end tell
```

### JSON Configuration Structure
Exported configurations include:
- Keyboard shortcuts mapping
- Ignored applications list
- Multi-monitor settings
- Custom layout definitions

## Integration Patterns

### With chezmoi
```bash
# Platform-specific Rectangle Pro configuration
{{- if eq .chezmoi.os "darwin" }}
# Apply Rectangle Pro settings via plist modification
{{- end }}
```

### Common Workflows
- Development setup: IDE left, terminal right, browser maximized
- Multi-monitor: Primary for code, secondary for communication
- Meeting mode: Video app centered, notes app in quarter

### Ignored Applications
Configure apps that shouldn't be managed:
- Virtual machines (Parallels, VMware)
- Games and fullscreen applications
- System utilities and menubar apps

## Advanced Configuration

### Percentage Layouts
Custom sizing beyond standard halves and quarters:
- 33%/67% splits for code review workflows
- 25%/50%/25% for three-column layouts
- Custom percentages for specific use cases

### Keyboard Shortcut Conflicts
Managing conflicts with system and application shortcuts:
- Disable conflicting macOS shortcuts in System Preferences
- Application-specific shortcut overrides
- Alternative modifier key combinations