# AI skill and plugin architecture

## Architecture overview

Chezmoi builds and registers skill and plugin packages from canonical sources.
The four stages below describe responsibilities; rendering and host filtering can run within the same external.

| Stage | Input and result | Source |
|---|---|---|
| Source and data | Authored files, pinned archives, and catalog selections combine with init data; effective data changes rendered content. | [Skills](skills/), [catalog](../chezmoi/.chezmoidata/ai/), [init template](../chezmoi/.chezmoi.toml.tmpl) |
| Generated packages | Preparation projects authored skills and plugins into native chezmoi entries; chezmoi renders `.tmpl` files, and versions follow content and selections. | [Projection](../python/skill_filter/skill_filter/agent_sources.py), [selection](../chezmoi/.chezmoitemplates/ai/agent-sources) |
| Host transformation and bundling | Externals select files, convert upstream agents, and build portable and host package views. | [Skill externals](../chezmoi/.chezmoiexternals/ai-skills.toml.tmpl), [agent externals](../chezmoi/.chezmoiexternals/ai-agents.toml.tmpl), [filter](../python/skill_filter/skill_filter/main.py) |
| Registration and uninstall | The post-apply bridge registers Claude Code and Codex packages and removes stale registrations that it owns. | [Hook](../chezmoi/.chezmoiscripts/run_after_agent-plugin-bridge.sh.tmpl), [bridge](../python/skill_filter/skill_filter/plugin_bridge.py) |

Authored skills and wrappers share the chezmoi Go template engine and effective data; there is no separate renderer or framework.
Chezmoi generates marketplace manifests from the catalog through the shared [`ai/plugin-marketplace`](../chezmoi/.chezmoitemplates/ai/plugin-marketplace) template.
Output paths below are relative to `chezmoi.destDir`.
Portable skills use `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills/`; host views use sibling `claude/`, `codex/`, and `cursor/` directories.
Cursor also receives local packages under `.cursor/plugins/local/`.
Antigravity reads flat skills from `.gemini/antigravity-cli/skills/` and package paths from `.gemini/config/plugins.json`; both require `local.bin.agy.installation_method != "none"`.
OpenCode V1 receives local package paths in `.config/opencode/opencode.json` when both its tool gate and the package gate are enabled.

## Workflows for AI agents

### Authored skills

Create `src/ai/skills/<name>/SKILL.md` for plain authored skill content, or `SKILL.md.tmpl` to use chezmoi Go templates.
Preparation discovers every skill directory that holds `SKILL.md` or `SKILL.md.tmpl`; a skill directory without either fails preparation.
A new skill deploys to every selected view without a catalog entry.
The [authored catalog](../chezmoi/.chezmoidata/ai/skills/authored.toml) holds exceptions only: `"absent"`, or one of `"claude"`, `"codex"`, `"cursor"`, and `"antigravity"`.
An exception for a skill without a source directory fails unless its value is `"absent"`.

The [`read-source-state.pre` hook](../chezmoi/.chezmoi.toml.tmpl) runs the [preparation launcher](../python/skill_filter/prepare-agent-sources.sh) before chezmoi reads the source state.
The [projection module](../python/skill_filter/skill_filter/agent_sources.py) writes native chezmoi source entries for every view into `src/chezmoi`, all or nothing, and lists them in `src/chezmoi/.agent-sources-manifest.json`.
These generated paths are gitignored; edit the canonical sources, never the generated entries.
A failed preparation stops chezmoi and keeps the previous generated tree.

| Generated source path in `src/chezmoi` | Target view |
|---|---|
| `dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills/exact_<name>/` | Portable package |
| `dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/<host>/skills/exact_<name>/` | Claude, Codex, and Cursor packages |
| `dot_cursor/plugins/local/mkobit-dotfiles/skills/exact_<name>/` | Cursor local package |
| `dot_gemini/antigravity-cli/skills/exact_<name>/` | Antigravity |
| `.chezmoidata/agent-source-inventory.json` | Data key `agent_source_inventory` |

Generated subdirectory `.chezmoiignore.tmpl` files drop unselected views through [`ai/agent-source-ignore`](../chezmoi/.chezmoitemplates/ai/agent-source-ignore), which reads the selection from [`ai/agent-sources`](../chezmoi/.chezmoitemplates/ai/agent-sources).
Host views follow `ai.plugin_bridge.default_hosts`, or `ai.plugin_bridge.capabilities.mkobit-dotfiles.hosts` when set; Antigravity also requires `local.bin.agy.installation_method != "none"`.
When the Antigravity gate is off, the generated ignore file hides every child, but chezmoi still creates `.gemini/antigravity-cli/skills/` as an empty directory.
The plugin bridge payload and the capability cleanup use the same effective mkobit-dotfiles hosts.
An external skill with the same name as a bare skill fails at template time, because a deselected bare skill's ignore pattern would hide it.
`agent_source_inventory` is a reserved data key that preparation generates; never set it in `.chezmoi.toml.tmpl` or `.chezmoidata/`.
A missing inventory renders as empty, so `chezmoi init` stays valid before the first preparation.

Canonical names deploy literally: preparation encodes leading dots and names that look like chezmoi attributes, and keeps executable modes and empty files.
Each skill root is `exact_`, so a deleted or renamed source file is removed on the next apply; the shared `skills/` directories stay non-exact because upstream archive externals also write there.
Only authored skill files with a final `.tmpl` suffix use template rendering; that suffix is removed from the output name.
A template that renders empty output is not deployed.
Source files that map to the same output path cause preparation to fail.

Chezmoi renders generated templates natively with the effective merged data from `.chezmoidata/` and `[data.*]` configuration.
Configuration values take precedence over catalog defaults at the same key path.
`chezmoi.sourceFile` is the generated source path, for example `dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills/exact_<name>/SKILL.md.tmpl`, and `chezmoi.targetFile` is the absolute target path.
Use `chezmoi.destDir` for destination paths and `dig` with safe defaults for optional data.
Use deterministic data; clocks, random values, and live lookups can change package versions on each apply.
The [base version template](../chezmoi/.chezmoitemplates/ai/authored-base-version) calculates the bundle version from inventory tree digests, selections, external skill selections, and rendered digests of templates in selected skills.
The [plugin manifest](../chezmoi/.chezmoitemplates/ai/authored-plugin-manifest) calculates authored plugin versions the same way; see [Authored plugin packages](#authored-plugin-packages).

The [technical-writing template](skills/technical-writing/SKILL.md.tmpl) accepts optional `ai.skills.content.technical-writing.description` and `ai.skills.content.technical-writing.instructions` strings.
A non-empty description replaces the YAML description with a quoted scalar.
Non-empty instructions follow the unchanged Markdown body after a blank line.
Missing or empty values keep the original description and body bytes.
Catalog defaults use `[ai.skills.content.technical-writing]`; an overlay can override either value in its init template:

```toml
[data.ai.skills.content.technical-writing]
description = "Use when writing standalone documentation."
instructions = "Follow the project style guide."
```

Rendered output uses the existing portable, host, Cursor local, and gated Antigravity paths described above.
The [root cleanup](#deselecting-or-removing-skills) removes deleted and deselected roots.
The [plugin bridge](../python/skill_filter/skill_filter/plugin_bridge.py) registers the generated packages after apply.
Rendering leaves canonical sources unchanged; edit those sources, not deployed copies.
Third-party packages, host conversion, and native package registration keep their existing behavior.

### Upstream third-party skills

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

### Authored plugin packages

Each directory `src/overlay-plugins/<dir>/` with an identity file `plugin.json` is one plugin; preparation discovers it, so it needs no catalog entry.
A plugin directory without `plugin.json` fails preparation.

| Identity key | Meaning |
|---|---|
| `description` | Required; copied into every generated manifest and marketplace entry. |
| `name` | Installed plugin name; defaults to the directory name. `mkobit-dotfiles` is reserved for the bare-skill bundle. |
| `skills_source_dir` | Exception: a shared skill root such as `src/overlay-skills`, instead of `<dir>/skills/`. The leading `src/` names the authored root of the tree that preparation reads, which in an overlay is the assembled tree, not the checkout. |
| `native_source` | `true` marks the skills tree and every wrapper directory as native chezmoi source. |
| `native_wrappers` | A list of hosts whose `wrappers/<host>/` directories are native chezmoi source. |
| `author`, `interface` | Optional objects copied verbatim into the Codex manifest only. |

```json
{
  "name": "mikekobit-writing",
  "description": "Writing skills.",
  "native_wrappers": ["cursor"]
}
```

Skills are the directories below `skills/` (or `skills_source_dir`) that hold `SKILL.md` or `SKILL.md.tmpl`.
Optional host files live below `wrappers/claude/`, `wrappers/codex/`, and `wrappers/cursor/`.
Source-only files such as `AGENTS.md` and `README.md` at the plugin root stay out of the package.

Preparation projects every plugin into native chezmoi entries for every host view:

| Generated source path in `src/chezmoi` | Target view |
|---|---|
| `dot_local/share/agent-plugins/marketplace/plugins/exact_<name>/exact_<host>/` | Claude, Codex, and Cursor packages |
| `dot_cursor/plugins/local/exact_<name>/` | Cursor local package |

Each view has a generated manifest `.<host>-plugin/plugin.json.tmpl` that calls [`ai/authored-plugin-manifest`](../chezmoi/.chezmoitemplates/ai/authored-plugin-manifest).
The manifest holds `name`, `version`, and `description`, `"skills": "./skills"` when the host has selected skills, and the components that the wrapper carries: `"mcpServers": "./.mcp.json"` for a wrapper `.mcp.json` and `"rules": "./rules"` for a wrapper `rules/` directory.
The version is `1.0.0+` and 12 hex digits of a digest of the inventory plugin digest, the selection, and the rendered bytes of every selected template, so it changes with content and data only.
A wrapper file at `.<host>-plugin/plugin.json` or below `skills/` fails preparation, because the manifest and skills are generated.
Custom wrapper files, such as a `.mcp.json.tmpl` server list or Cursor `rules/`, are the canonical exceptions that stay in `wrappers/<host>/`.

[`ai/agent-sources`](../chezmoi/.chezmoitemplates/ai/agent-sources) joins the inventory with these control-plane exceptions; the generated ignore views drop everything that it does not select:

| Exception | Default |
|---|---|
| `ai.plugin_bridge.capabilities.<name>.hosts` | `ai.plugin_bridge.default_hosts` |
| `ai.plugin_bridge.capabilities.<name>.environments` against `ai.plugin_bridge.environment` | every environment |
| `ai.plugin_bridge.capabilities.<name>.skills.<skill>` = `"absent"` or a host | `"present"` |
| `ai.plugin_bridge.capabilities.<name>.marketplace` | `dotfiles` |

```toml
[data.ai.plugin_bridge.capabilities.toolshed-mcp]
hosts = ["claude", "codex"]

[data.ai.plugin_bridge.capabilities.stripe-dotfiles.skills]
jira-slack-to-jira = "absent"
```

An exception for an unknown skill fails unless its value is `"absent"`.
The Cursor local package exists only when Cursor is a selected host.
Unselected hosts, absent skills, and disabled environments are ignored before rendering, so their templates never run.
[`ai/plugin-bridge`](../chezmoi/.chezmoitemplates/ai/plugin-bridge) adds each enabled plugin to the marketplaces and the bridge payload with its description, marketplace, and selected hosts, then applies any data keys of the same name.
A plugin name that equals an upstream or bundle capability (`external_source` or `acquisition_destination`) fails.

Literal trees deploy names as written: preparation encodes leading dots and attribute-like names and keeps executable modes and empty files.
A native tree is copied verbatim as chezmoi source, so `exact_`, `private_`, `readonly_`, `empty_`, `executable_`, `dot_`, `literal_`, the `.tmpl` suffix, and `.keep` placeholders keep their chezmoi meaning.
Native entries cannot use `create_`, `modify_`, `remove_`, `run_`, `symlink_`, `external_`, `encrypted_`, `once_`, `onchange_`, `before_`, `after_`, or `.chezmoi*` names.
Preparation always makes the plugin root, each host root, `skills/`, and each skill root exact; nested native directories are exact only when the author writes `exact_`.

The exact boundary: while a plugin view is managed, chezmoi deletes every unmanaged file inside its plugin root, including files that a user adds.
Never put local notes in a deployed plugin directory.
Chezmoi keeps ignored entries inside an exact directory, so a deselected host, skill, or plugin stays in the destination until root ownership cleanup removes it.
The marketplace `plugins/` directory, `.cursor/plugins/local/`, and the `mkobit-dotfiles` host and `skills/` directories are shared and never exact.

Cursor can discover skills from other host paths, so leaving a plugin out of the Cursor views does not guarantee that Cursor cannot see its skills.
The host selection limits installation, not discovery.

`mkobit-dotfiles` has no identity file: it keeps its bridge declaration and canonical manifest templates, because its package also holds upstream archive skills.

### Deselecting or removing skills

Authored skills and plugins converge without catalog keys.
Delete a skill or plugin source, deselect a host, set a skill exception to `"absent"`, or disable a plugin environment, and the next apply removes the deployed root.
Upstream skills in `src/chezmoi/.chezmoidata/ai/skills/<source>.toml` still need state `"absent"`; their `.chezmoiremove.tmpl` tombstones prune the installed copy, so never delete those keys.

chezmoi keeps ignored entries inside `exact_` directories, so deselected roots stay deployed until the [root cleanup](../chezmoi/.chezmoiscripts/run_onchange_after_00-agent-source-root-cleanup.sh.tmpl) runs.
The script records the roots it owns in `~/.local/state/dotfiles/agent-source-roots.json`.
Each run removes `previous roots - desired roots - protected roots`, deepest first, through the [cleanup module](../python/skill_filter/skill_filter/agent_source_cleanup.py).
It commits the new state only after every removal succeeds, so a failed removal retries on the next apply.
Protected roots are external skills from `ai.skills.external`; shared host skill directories and marketplaces are never roots.
The module rejects roots outside its allowed patterns and symlinked path components.
The old `agent-plugin-capability-ownership.json` file is mapped to roots once, then deleted; roots that are still desired, and files of the mkobit-dotfiles bundle manifests, stay.
Plugin registrations leave through the plugin bridge ownership rules.

Boundary: removing an owned root deletes every file inside it, including files a user added there.
Put unmanaged files outside owned skill and plugin roots.
Only `example_skill` keeps an `"absent"` key in the authored catalog; it stays in the repository and deploys nowhere.

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
Each marketplace has one source template per native host, which calls the shared renderer.
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

Apply never updates an external catalog.
Archive packages change only when their catalog pins change, and the bridge skips `plugin add` for a Codex package plugin that is installed, enabled, and at the version in the deployed `.codex-plugin/plugin.json`.
Package versions derive from content digests, so an equal version means equal content.
The bridge installs and enables a plugin from a `host-provided` marketplace when it is missing, but never updates, uninstalls, or records it.
It does not re-enable a disabled host-provided Codex plugin that it did not install, because Codex can enable only by adding again; it logs `event=skip-reenable` instead.

### Refreshing external catalogs

Set `DOTFILES_AGENT_PLUGIN_REFRESH=1` for one apply, or run `plugin_bridge.py reconcile --destination D --refresh`, to refresh external catalogs.
Refresh covers marketplaces with `source_type` `public` or `internal` that the bridge owns, meaning it registered them; it skips registrations that a user added.
Per host, it runs `plugin marketplace update` (Claude) or `plugin marketplace upgrade` (Codex).
It then updates the owned plugins of those marketplaces: Claude runs `plugin update`, and Codex removes and adds a plugin when its installed version differs from the refreshed catalog.
Refresh never touches `host-provided` marketplaces such as the corporate wrapper, or `generated` marketplaces such as pinned archives.
Apply without the variable adds an absent `public` or `internal` marketplace and never updates a present one.
`DISABLE_AUTOUPDATER = "true"` in `.chezmoidata/claude_code.toml` stays unchanged; whether to set `FORCE_AUTOUPDATE_PLUGINS` is a separate proposal.

## Upstream agents

Agents follow the pin-and-select model via `src/chezmoi/.chezmoidata/ai/agents.toml` and `src/chezmoi/.chezmoiexternals/ai-agents.toml.tmpl`.
Claude Code receives raw markdown files under `~/.claude/agents/<source>/`.
Antigravity and Cursor consume agents rewritten to `SKILL.md` format by `skill_filter`.
OpenCode receives agents under `~/.config/opencode/agents/<source>/` rewritten with explicit `name` and `mode: subagent`.
Onboarding an agent requires a prompt-injection review of content at the pinned ref.

## Verification and testing

Preview pending changes:

```sh
chezmoi diff
```

Apply skill and plugin updates:

```sh
chezmoi apply
```

Validate an overlay with its real assembly and `chezmoi init` in a temporary destination, with separate config, cache, and state paths.
Then run a scoped `chezmoi apply` that excludes installation and native registration scripts.
Inspect manifest resource paths and complete Cursor local copies in the output.
An offline check that excludes remote externals verifies authored packages only; it does not verify remote acquisition or remote installation.

Run the focused package tests and linters:

```sh
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest -p no:cacheprovider -m 'not integration' tests/integration/test_ai_skills.py tests/integration/test_ai_authored_capabilities.py tests/integration/test_ai_plugin_manifest_lifecycle.py tests/integration/test_ai_environment_fixtures.py tests/integration/test_overlay_authored_manifest_snapshot.py tests/integration/test_sbx_plugin_approval.py tests/integration/test_opencode_plugins.py src/python/skill_filter/tests/
```
