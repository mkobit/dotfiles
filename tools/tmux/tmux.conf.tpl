# Modular TMux Configuration
# Auto-generated file - DO NOT EDIT DIRECTLY

# Core tmux settings
{{include_core}}

# Display settings
{{include_display}}

# Keybindings 
{{include_keybindings}}

# Mouse settings
{{include_mouse}}

# Copy mode settings
{{include_copy_mode}}

# Platform-specific settings
{{include_platform_specific}}

# Source local overrides if present
if-shell "[ -f ~/.tmux.conf.local ]" "source ~/.tmux.conf.local"