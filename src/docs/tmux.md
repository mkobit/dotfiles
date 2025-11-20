# tmux Configuration

Tmux configuration is managed declaratively through snippets and plugins, without using TPM (Tmux Plugin Manager).

## Architecture

### Configuration Loading Order

1. **Snippets** (`$CHEZMOI_DEST/.dotfiles/tmux/snippets/*.tmux`) - Base configuration
   - Loaded first in alphabetical order
   - Provides core tmux settings, keybindings, and styling
   - See `src/dot_dotfiles/tmux/config.tmux.tmpl` for the source pattern

2. **Plugins** (`$CHEZMOI_DEST/.dotfiles/tmux/plugins/*/*.tmux`) - Plugin initialization
   - Loaded last, can override base configuration
   - Plugin `*.tmux` files are executed as bash scripts (mimics TPM behavior)
   - Managed via chezmoi externals with pinned commits

### Why Not TPM?

We avoid TPM (Tmux Plugin Manager) because:
- TPM fetches plugins at runtime from the internet
- Our approach uses chezmoi externals for offline, reproducible installations
- Plugins are pinned to specific commits for stability
- Entire plugin installation is managed declaratively

## Plugin Management

### Adding a New Plugin

1. **Create data file** at `src/.chezmoidata/tmux/plugins/<plugin-name>.toml`:
   ```toml
   [tmux.plugins.<plugin-name>]
   enabled = true
   commit = "abc123..."  # Specific git commit hash
   ```

2. **Create external** at `src/.chezmoiexternals/<plugin-name>.toml.tmpl`:
   ```toml
   {{- $plugin := index .tmux.plugins "<plugin-name>" -}}
   {{- if $plugin.enabled -}}
   [".dotfiles/tmux/plugins/<plugin-name>"]
       type = "archive"
       url = "https://github.com/author/plugin/archive/{{ $plugin.commit }}.tar.gz"
       exact = true
       stripComponents = 1
   {{- end -}}
   ```

3. **Apply configuration**: `chezmoi apply`

The plugin's `*.tmux` files will be automatically executed on tmux startup.

### Current Plugins

- **[tmux-powerline](https://github.com/erikw/tmux-powerline)** - Powerline status bar
  - Commit: `3a4a6886886aece965b359479fad35dd1fb1fd2b`
  - Overrides status-left and status-right configuration
  - See: `src/.chezmoidata/tmux/plugins/tmux-powerline.toml`

### Finding Plugins

- **[Official TPM Plugin List](https://github.com/tmux-plugins/list)** - Curated plugins
- **[Awesome tmux](https://github.com/rothgar/awesome-tmux)** - Comprehensive plugin collection

Note: Most TPM plugins have a `*.tmux` initialization script that works with our setup.

## Configuration Files

### Snippets Directory

Located at `src/dot_dotfiles/tmux/snippets/`, each file handles a specific concern:

- `status_bar_styling.tmux` - Colors, pane borders, message styling
- `copy_mode.tmux` - Vi-style copy mode keybindings
- `window_panes.tmux` - Window and pane management
- `mouse_support.tmux` - Mouse interaction settings
- `popups.tmux` / `popups_enhanced.tmux` - Popup window bindings
- `notifications.tmux` - Activity and bell notifications
- `terminal_settings.tmux` - Terminal compatibility settings
- `server_options.tmux` - Server-wide options
- `windows.tmux` - Window-specific settings
- `history.tmux` - History configuration
- `universal.tmux` - Universal keybindings
- `local_extensions.tmux` - Machine-specific overrides

### Main Configuration

- `src/dot_dotfiles/tmux/config.tmux.tmpl` - Main entry point
- `src/modify_dot_tmux.conf.tmpl` - Injects config into `~/.tmux.conf`

## Customization

### Machine-Specific Overrides

Use `local_extensions.tmux` for machine-specific customization:

```tmux
# Example: Different status position on laptop
%if "#{==:#{host},laptop}"
set -g status-position bottom
%endif
```

### Disabling Plugins

Set `enabled = false` in the plugin's data file and run `chezmoi apply`.

## Troubleshooting

### Plugin Not Loading

1. Check plugin is enabled in `src/.chezmoidata/tmux/plugins/<plugin>.toml`
2. Verify plugin downloaded: Check `$CHEZMOI_DEST/.dotfiles/tmux/plugins/<plugin>/`
3. Check for `*.tmux` files in the plugin directory
4. Reload tmux config: `tmux source-file $CHEZMOI_DEST/.tmux.conf`

### Status Bar Not Showing

- Plugins load after snippets and override base configuration
- Check `status_bar_styling.tmux` note about plugin overrides
- Verify tmux-powerline is enabled and installed

## References

- [tmux Manual](https://man.openbsd.org/tmux)
- [tmux Plugins List](https://github.com/tmux-plugins/list)
- [Awesome tmux](https://github.com/rothgar/awesome-tmux)
- [tmux-powerline Configuration](https://powerline.readthedocs.io/en/latest/configuration.html)
- [Chezmoi Externals](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/)
