# AI plugins, skills, and agents

Chezmoi manages the AI capabilities used by the supported tools.
The repository generates local plugins and marketplaces, selects third-party capabilities, and registers them with each tool.

## Authored capabilities

[Plugin source folders](../chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/) contain authored skills and other plugin files.
Each plugin has an identity in the [plugin catalog](../chezmoi/.chezmoidata/ai/plugins/).
Chezmoi renders host manifests and a local marketplace from these sources using the [AI templates](../chezmoi/.chezmoitemplates/ai/).
Overlays can add plugins and change which capabilities and hosts are enabled.

## Third-party capabilities

The [marketplace catalog](../chezmoi/.chezmoidata/ai/plugin-bridge.toml) supports generated, public, internal, and host-provided marketplaces and their plugins.
Host-provided marketplaces remain under the host's control.
Complete upstream plugin archives are pinned and retain their upstream files, including hooks and agents.
See the [plugin external](../chezmoi/.chezmoiexternals/ai-upstream-plugins.toml.tmpl) and [plugin catalog](../chezmoi/.chezmoidata/ai/plugins/).

The [skill catalog](../chezmoi/.chezmoidata/ai/skills/) selects individual upstream skills from archives pinned by commit and checksum.
Selected skills currently enter the `mkobit-dotfiles` plugin.
The [agent catalog](../chezmoi/.chezmoidata/ai/agents.toml) selects upstream agents separately.
Review upstream skills and agents at their pinned commit before adding them.

## Tool delivery

The [plugin bridge](../python/skill_filter/skill_filter/plugin_bridge.py) registers marketplaces and plugins through the Claude Code and Codex CLIs.
Cursor receives local plugin copies.
Antigravity uses `agy` to install plugin directories and can also receive selected skills directly.
Selected upstream agents are delivered as native agents for Claude Code, native roles for Codex, or skills for Cursor and Antigravity.
The [agent external](../chezmoi/.chezmoiexternals/ai-agents.toml.tmpl) defines these transformations.

See [AI checks](TEST.md) for validation and tests.
