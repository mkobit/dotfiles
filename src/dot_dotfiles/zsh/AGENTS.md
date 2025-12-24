# Zsh configuration

This repository supports both Zsh (primary) and Bash environments.

## Shell configuration

Common shell logic is maintained in `src/.chezmoitemplates/shell/` and included in shell-specific scripts using chezmoi templates.

### Shared templates

Templates in `src/.chezmoitemplates/shell/` contain the core logic. These scripts are designated to avoid duplication while allowing for shell-specific rendering.

### Usage

To use a shared template in a shell configuration:
1. Create a script in the shell's specific directory (e.g., `src/dot_dotfiles/zsh/scripts/` or `src/dot_dotfiles/bash/snippets/`).
2. Use the `.tmpl` extension.
3. Include the shared template, passing the shell context and preserving the global context:
   ```
   {{ template "shell/template_name.sh" (merge (dict "shell" "zsh") .) }}
   ```

### Template logic

Templates in `src/.chezmoitemplates/shell/` should use the `.shell` variable to conditionally render content and fail on unsupported shells:
```bash
{{- if eq .shell "zsh" }}
# Zsh specific code
{{- else if eq .shell "bash" }}
# Bash specific code
{{- else }}
{{- fail (printf "unsupported shell: %s" .shell) }}
{{- end }}
```

### Zsh specifics

Zsh-specific scripts are in `src/dot_dotfiles/zsh/scripts/`.
They are sourced in lexicographical order (numeric prefix recommended).

## Oh My Zsh

Oh My Zsh is a framework for managing zsh configuration with themes, plugins, and community-driven enhancements.

### Installation method

This dotfiles setup uses chezmoi's external sources to install oh-my-zsh:
- Downloads from the official GitHub repository
- Installs to a managed path

### Configurability options

For detailed configuration options and settings, see:
- [Oh My Zsh Settings Wiki](https://github.com/ohmyzsh/ohmyzsh/wiki/Settings)
- [Themes Documentation](https://github.com/ohmyzsh/ohmyzsh/wiki/Themes)
- [Plugins Documentation](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)

Key configurable environment variables include:
- `ZSH_CACHE_DIR` - Custom cache directory location
- `ZSH_THEME` - Theme selection
- `DISABLE_AUTO_UPDATE` - Update behavior
- Plugin configuration via `plugins=()` array

## Powerlevel10k

Fast, customizable Zsh theme. See [GitHub](https://github.com/romkatv/powerlevel10k) for full documentation.

**Status**: Currently disabled - using robbyrussell theme instead.

### Configuration

1. Start new shell: `exec zsh`
2. Follow configuration wizard (auto-starts)
3. Or run manually: `POWERLEVEL9K_CONFIG_FILE=/tmp/p10kconfig.zsh p10k configure`

Creates `~/.p10k.zsh` - add to chezmoi if you want to version it.

#### Configuration file management
- **Default location**: `~/.p10k.zsh`
- **Custom location**: Set `POWERLEVEL9K_CONFIG_FILE` environment variable
- **Reference**: [GitHub Issue #967](https://github.com/romkatv/powerlevel10k/issues/967) - Configuration file location

### Font requirement

**MesloLGS NF fonts are automatically downloaded** to `~/.dotfiles/external/fonts/` with SHA verification.

Manual installation: Install a [Nerd Font](https://github.com/romkatv/powerlevel10k#fonts) for proper icons.

### iTerm2 font configuration (future)

When Powerlevel10k is re-enabled, an automated iTerm2 configuration script can be used:

#### iTerm2 profile configuration
Use PlistBuddy to configure font settings (from wizard source):

```bash
plist=~/Library/Preferences/com.googlecode.iterm2.plist
size=13  # P10k wizard bumps 12 to 13

# Key settings (Try Set, fallback to Add)
/usr/libexec/PlistBuddy -c "Set :\"New Bookmarks\":0:\"Normal Font\" \"MesloLGS-NF-Regular $size\"" "$plist"
/usr/libexec/PlistBuddy -c "Set :\"New Bookmarks\":0:\"Draw Powerline Glyphs\" 1" "$plist"

# Refresh settings cache
/usr/bin/defaults read com.googlecode.iterm2 >/dev/null
```

#### Implementation files
- Font downloads: `.chezmoiexternal.toml.tmpl` (MesloLGS NF variants with SHA256)
- iTerm config: `run_onchange_configure-iterm-font.sh.tmpl` (disabled for now)
- P10k config: `dot_dotfiles/zsh/oh-my-zsh/p10k.zsh` (add to source control when ready)
