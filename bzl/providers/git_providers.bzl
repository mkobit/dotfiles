"""Provider definitions for Git configuration."""

# Define the GitConfigInfo provider to make configuration data strongly typed
GitConfigInfo = provider(
    doc = "Information about Git configuration",
    fields = {
        "settings": "Dictionary of git settings organized by section",
        "aliases": "Dictionary of git aliases",
        "includes": "List of other git configs to include",
        "platform_specific": "Platform-specific settings",
        "raw_sections": "Raw git config sections to include",
        "variant_settings": "Variant-specific settings (work, personal, etc.)",
    },
)