# Powerlevel10k

Fast, customizable Zsh theme. See [GitHub](https://github.com/romkatv/powerlevel10k) for full documentation.

**Status**: Currently disabled - using robbyrussell theme instead.

## Configuration

1. Start new shell: `exec zsh`
2. Follow configuration wizard (auto-starts)
3. Or run manually: `POWERLEVEL9K_CONFIG_FILE=/tmp/p10kconfig.zsh p10k configure`

Creates `~/.p10k.zsh` - add to chezmoi if you want to version it.

### Configuration File Management
- **Default location**: `~/.p10k.zsh`
- **Custom location**: Set `POWERLEVEL9K_CONFIG_FILE` environment variable
- **Reference**: [GitHub Issue #967](https://github.com/romkatv/powerlevel10k/issues/967) - Configuration file location

## Font Requirement

**MesloLGS NF fonts are automatically downloaded** to `~/.dotfiles/external/fonts/` with SHA verification.

Manual installation: Install a [Nerd Font](https://github.com/romkatv/powerlevel10k#fonts) for proper icons.

## iTerm2 Font Configuration (Future)

When Powerlevel10k is re-enabled, an automated iTerm2 configuration script can be used:

### Font Installation Script
Based on [Powerle

### iTerm2 Profile Configuration
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

### Implementation Files
- Font downloads: `.chezmoiexternal.toml.tmpl` (MesloLGS NF variants with SHA256)
- iTerm config: `run_onchange_configure-iterm-font.sh.tmpl` (disabled for now)
- P10k config: `dot_dotfiles/zsh/oh-my-zsh/p10k.zsh` (add to source control when ready)
