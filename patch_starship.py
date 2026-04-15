import tomli
import tomli_w
import os

with open('./src/chezmoi/dot_config/starship.toml', 'rb') as f:
    config = tomli.load(f)

# The user wants to display vault name
# I will use a custom obsidian module in starship
if "custom" not in config:
    config["custom"] = {}

config["custom"]["obsidian"] = {
    "command": "get-obsidian-vault.sh",
    "when": "get-obsidian-vault.sh > /dev/null",
    "format": "on [󰎚 $output]($style) ",
    "style": "bold purple"
}

# The user wants this to be appended to the prompt
# To properly configure where it appears, I should look at the "format" string in the config if it exists
# Starship has a default format, and if we just add a module it's appended or placed based on `format` or by default it's appended with all other custom modules
# We don't have to define `format` globally unless we want to control the exact position.
# Let's check if the format is defined.

with open('./src/chezmoi/dot_config/starship.toml', 'wb') as f:
    tomli_w.dump(config, f)
