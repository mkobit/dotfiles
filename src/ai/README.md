# AI skill and plugin architecture

## Architecture overview

Three layers deliver agent plugins and skills; they do not mix.

| Layer | What it does | Source |
|---|---|---|
| Generate | `chezmoi apply` writes the authored plugin packages from native source folders. Files only; templates fill in manifests, versions, and capabilities. | [Plugin folders](../chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/), [host templates](../chezmoi/.chezmoitemplates/ai/) |
| External | Third-party skills, plugins, and agents come only through pinned chezmoi externals. | [Catalog](../chezmoi/.chezmoidata/ai/), [skill externals](../chezmoi/.chezmoiexternals/ai-skills.toml.tmpl), [plugin externals](../chezmoi/.chezmoiexternals/ai-upstream-plugins.toml.tmpl), [agent externals](../chezmoi/.chezmoiexternals/ai-agents.toml.tmpl) |
| Install and link | After the files are written, the `run_after` bridge installs and removes plugins through each host CLI. It never writes package files. | [Hook](../chezmoi/.chezmoiscripts/run_after_agent-plugin-bridge.sh.tmpl), [bridge](../python/skill_filter/skill_filter/plugin_bridge.py) |

Output paths below are relative to `chezmoi.destDir`.
The generated `dotfiles` marketplace is `.local/share/agent-plugins/marketplace/`.
It holds `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` (Codex), `.cursor-plugin/marketplace.json`, and `plugins/<name>/`.
Dotfiles own `plugins/`, so a plugin folder that leaves the source leaves the destination.

## Authored plugins

### Layout

Each authored plugin is one folder, `src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_<name>/`.
Hosts share the folder where their layouts allow, because each host reads only its own `.<host>-plugin/` manifest:

```text
exact_mkobit-dotfiles/
├── exact_dot_claude-plugin/plugin.json.tmpl   → .claude-plugin/plugin.json
├── exact_dot_codex-plugin/plugin.json.tmpl    → .codex-plugin/plugin.json
├── exact_dot_cursor-plugin/plugin.json.tmpl   → .cursor-plugin/plugin.json
├── plugin.json.tmpl                           → plugin.json (Antigravity)
├── exact_claude/exact_skills/.keep            → claude/skills/ (Claude-only upstream skills)
└── exact_skills/
    ├── exact_beads/SKILL.md
    └── exact_technical-writing/SKILL.md.tmpl
```

Use `exact_` on every folder so that deleted and renamed files go on the next apply.
Use chezmoi source names for files: `dot_` for dotfiles, `executable_` for scripts, and `.tmpl` for templates, which render with the normal data.
Each manifest is one line that calls the template of its host:

```text
{{ includeTemplate "ai/claude/plugin-manifest" (dict "name" "mkobit-dotfiles" "root" .) -}}
```

Pass `"extra" (dict "mcpServers" "./.mcp.json")` to add host manifest keys, such as MCP servers or Cursor `rules`.
When a host needs a different shape, put its package in a host subfolder, for example `exact_<name>/exact_claude/`, and name it in `host_dirs` (see below).
The marketplace then points that host at `./plugins/<name>/<dir>`.
The [Codex template](../chezmoi/.chezmoitemplates/ai/codex/plugin-manifest) lists the skill names as `interface.capabilities`.
Versions digest the folder contents, rendered templates, and selection data, so they change with content and data only.

### Data

Identity is one table per plugin in `src/chezmoi/.chezmoidata/ai/plugins/<name>.toml`:

```toml
[ai.plugins.example]
description = "Example plugin."
author = "someone"         # optional; defaults to .chezmoi.username
[ai.plugins.example.host_dirs]
claude = "claude"          # optional; the package of this host is plugins/example/claude
```

Skills are discovered from the folder, never listed.
An authored identity table has no archive keys, so the upstream plugin external ignores it.
Machine decisions live in the init template, with safe defaults when absent:

```toml
[data.ai.plugin_bridge]
default_hosts = ["claude", "codex", "cursor"]

[data.ai.plugin_bridge.capabilities.example]
enabled = false                 # default true; false removes the plugin
hosts = ["claude", "codex"]     # default ai.plugin_bridge.default_hosts
environments = ["mydev"]        # default every ai.plugin_bridge.environment

[data.ai.plugin_bridge.capabilities.example.skills]
some-skill = "absent"
```

A deselected host manifest renders empty, so chezmoi removes it.
[`ai/plugin-ignore`](../chezmoi/.chezmoitemplates/ai/plugin-ignore) ignores disabled plugins, unselected host subfolders, and absent skills.
chezmoi keeps ignored entries inside `exact_` folders, so a [small script](../chezmoi/.chezmoiscripts/run_onchange_before_00-agent-plugin-deselect.sh.tmpl) moves deployed copies to `.local/state/dotfiles/agent-plugin-deselected/` and back when they are selected again.
A disabled plugin leaves the marketplaces, and the bridge uninstalls it when it owns the install.

### Overlay contract

An overlay adds plugins and changes choices; it never edits base files outside its `OVERLAY_WINS` list.

- Add a plugin: add `exact_plugins/exact_<name>/` to the overlay `src/chezmoi`, and `.chezmoidata/ai/plugins/<name>.toml`. `bin/assemble` merges the folders.
- Change a choice: set `[data.ai.plugin_bridge]` or `[data.ai.plugin_bridge.capabilities.<name>]` keys in the overlay `.chezmoi.toml.tmpl`, for example `enabled = false` for a base plugin or `local.bin.agy.installation_method = "none"`.
- An overlay `.chezmoiignore.tmpl` must keep `{{ includeTemplate "ai/plugin-ignore" . }}`; an overlay `dot_claude/.chezmoiremove.tmpl` should range over `ai/retired-skills`.

### Hosts

Claude Code and Codex install through their plugin CLIs; the bridge records ownership only for installs it performed.
Cursor has no plugin install command, so no bridge adapter exists for it.
[`run_onchange_after_agent-plugin-cursor-local`](../chezmoi/.chezmoiscripts/run_onchange_after_agent-plugin-cursor-local.sh.tmpl) copies each enabled authored plugin selected for Cursor from the marketplace folder to `.cursor/plugins/local/<name>/` (with `.cursor-plugin/plugin.json`), and removes the copy of a plugin that is disabled or not selected.
Antigravity converges only through the `agy` CLI, never through `.gemini/config/plugins.json`.
When `local.bin.agy.installation_method` is not `"none"`, the bridge runs `agy plugin list --json` and compares it with the plugin directories that have `plugin.json` or `.antigravity-plugin/plugin.json` at their root.
Those are the authored `dotfiles` plugins, and the Superpowers directory when chezmoi installs it; upstream Superpowers ships its own `.antigravity-plugin/plugin.json`, so chezmoi generates no manifest for it.
The bridge runs `agy plugin install <plugin dir>` for a missing plugin.
It runs `agy plugin uninstall <name>` then install when the listed version differs from the generated manifest version.
It records ownership (`plugin`, `antigravity`) in the same ownership file for each install, and uninstalls an owned plugin that is no longer desired.
It never uninstalls a plugin that it did not install.
The list parser accepts a top-level array or an object with a `plugins`, `installed`, `items`, `entries`, or `data` array, with entries that have `name` and optional `version`.
If `agy` is missing, a probe or command fails, or the list is unparseable, the bridge logs and skips agy for that run; apply never fails because of agy.
A plugin installed by an earlier bridge run has no ownership record, so the bridge reinstalls it on a version change but never uninstalls it.
`dot_gemini/config/modify_plugins.json` only removes the old `plugins.json` entries and can be deleted later.
The bridge refreshes owned external marketplaces only with its `--refresh` flag or chezmoi's `-R` (`--refresh-externals`) flag from `CHEZMOI_ARGS`.

### Skill templates

The [technical-writing template](../chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_technical-writing/SKILL.md.tmpl) accepts optional `ai.skills.content.technical-writing.description` and `ai.skills.content.technical-writing.instructions` strings.
A non-empty description replaces the YAML description; non-empty instructions follow the body after a blank line.
An overlay can set either value in its init template:

```toml
[data.ai.skills.content.technical-writing]
description = "Use when writing standalone documentation."
instructions = "Follow the project style guide."
```

## Upstream third-party skills

Pin `repo`, `ref`, and `sha256` under `[ai.skills.external.<source>]` in `src/chezmoi/.chezmoidata/ai/skills/<source>.toml`.
Select individual skills under `[ai.skills.external.<source>.skills]` with state `"present"` or a specific host name (`"claude"`, `"codex"`, `"cursor"`, `"antigravity"`).

```toml
[ai.skills.external.example]
repo = "<owner>/<repo>"
ref = "<full commit sha>"
sha256 = "<sha256 of downloaded archive>"

[ai.skills.external.example.skills]
example = "present"
```

Compute the pin for a new commit with `curl`:

```sh
curl -sL https://codeload.github.com/<owner>/<repo>/tar.gz/<commit-sha> | sha256sum
```

Set `skill_file = "SKILL.md"` on single-skill repositories shipping `SKILL.md` at archive root instead of under `skills_root/<name>/`.

### Internal GitHub Enterprise or corporate proxy

Declare a custom archive host under `[ai.skills.hosts.<host>]` in `src/chezmoi/.chezmoidata/ai/hosts.toml` or in an overlay using `url_format` with `{repo}` and `{ref}` tokens.
Set explicit `url` on a source table under `[ai.skills.external.<source>]` for one-off published archives.

```toml
[ai.skills.hosts.ghe]
url_format = "https://ghe.internal/api/v3/repos/{repo}/tarball/{ref}"
```

A `"present"` upstream skill deploys to `plugins/mkobit-dotfiles/skills/<name>`, and also to `.gemini/antigravity-cli/skills/<name>` when Antigravity is enabled.
A host state such as `"claude"` deploys to `plugins/mkobit-dotfiles/claude/skills/<name>`, which only the Claude manifest lists.
Set a deselected skill to `"absent"` so the host `.chezmoiremove.tmpl` files prune copies, then delete the key after about two months; machines that apply later clean leftovers by hand.
Retired authored skill names live in [`ai/retired-skills`](../chezmoi/.chezmoitemplates/ai/retired-skills).

## Upstream plugin packages

Declare archive metadata under `[ai.plugins.<name>]` in `src/chezmoi/.chezmoidata/ai/plugins/<name>.toml`.
Enable the package in the init template:

```toml
[data.ai.plugins.superpowers]
installation_method = "chezmoi_external"
```

Set the method to `"none"` to remove the managed package and its host registrations.
A missing method also means `"none"`.
The archive pin uses a full commit ref and archive SHA-256.
Archive hosts use the existing `ai.skills.hosts` catalog, so an overlay can select its package mirror.

[Superpowers v7.0.0](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3) deploys the complete repository, with no skill filter or workflow edits.
Its shared root is `.local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers/`.
Claude Code and Codex register it as `superpowers@superpowers-marketplace`, separate from `mkobit-dotfiles@dotfiles`.
Each generated marketplace declares its destination-relative `source_locator`, owner, source, trust class, and native hosts in the keyed marketplace catalog.
[`plugin_declarations.py`](../python/skill_filter/skill_filter/plugin_declarations.py) validates and plans declarations without file writes.
Each marketplace has one source template per host, which calls that host's template under `.chezmoitemplates/ai/<host>/`.
Overlays can add marketplace templates and catalog declarations through the same structure.
Provenance reports each capability's marketplace, source, and trust class from its own declaration.
Cursor receives an identical archive at `.cursor/plugins/local/superpowers/` and uses the upstream manifest and hooks there.
The [upstream OpenCode adapter](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/.opencode/INSTALL.md) uses the shared root as an absolute local package directory in the pinned V1 `plugin` array.
OpenCode registration also requires `local.bin.opencode.installation_method != "none"`.
OpenCode retires only the old managed Superpowers package reference and preserves unrelated plugin entries.
Antigravity adds the enabled Superpowers package parent directory and keeps its existing dotfiles registration and tool gate.
Gemini CLI stays disabled where its tool gate is absent or set to `"none"`.
The package retains upstream rules, agents, hooks, and runtime helpers.
Legacy per-skill Superpowers selections stay `"absent"` so apply removes duplicate copies.

## Upstream agents

Agents follow the pin-and-select model via `src/chezmoi/.chezmoidata/ai/agents.toml` and `src/chezmoi/.chezmoiexternals/ai-agents.toml.tmpl`.
Claude Code receives raw markdown files under `~/.claude/agents/<source>/`.
Antigravity and Cursor consume agents rewritten to `SKILL.md` format by `skill_filter`.
OpenCode receives agents under `~/.config/opencode/agents/<source>/` rewritten with explicit `name` and `mode: subagent`.
Onboarding an agent requires a prompt-injection review of content at the pinned ref.

## Verification and testing

Preview pending changes with `chezmoi diff`, then apply with `chezmoi apply`.
Validate an overlay with its real assembly and `chezmoi init` in a temporary destination, with separate config, cache, and state paths.
Then run a scoped `chezmoi apply --exclude scripts`, so that the bridge does not register temporary paths with the real host CLIs.

Run the focused tests and linters:

```sh
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest -p no:cacheprovider -m 'not integration' tests/integration/test_ai_plugin_folders.py tests/integration/test_ai_skills.py tests/integration/test_ai_environment_fixtures.py src/python/skill_filter/tests/
```
