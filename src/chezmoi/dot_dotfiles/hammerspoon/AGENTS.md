# Hammerspoon configuration

## Custom config directory

- **Default Override**: We override the default `~/.hammerspoon` path.
- **Location**: `{{ .chezmoi.destDir }}/.dotfiles/hammerspoon/init.lua`
- **Preference Key**: `MJConfigFile` is set to point to this location.

**Important**: Spoons are relative to this config file. Restart Hammerspoon after changing the path.
