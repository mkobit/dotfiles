# AI skill and plugin architecture

## Architecture overview

Chezmoi builds and registers skill and plugin packages from canonical sources.
The four stages below describe responsibilities; rendering and host filtering can run within the same external.

| Stage | Input and result | Source |
|---|---|---|
| Source and data | Authored files, pinned archives, and catalog selections combine with init data; effective data changes rendered content. | [Skills](skills/), [catalog](../chezmoi/.chezmoidata/ai/), [init template](../chezmoi/.chezmoi.toml.tmpl) |
| Generated packages | Packages contain copied plain files, rendered authored `.tmpl` files, and versions based on content and selections. | [File entries](../chezmoi/.chezmoitemplates/ai/authored-file-entry), [package inputs](../chezmoi/.chezmoitemplates/ai/authored-plugins) |
| Host transformation and bundling | Externals select files, convert upstream agents, and build portable and host package views. | [Skill externals](../chezmoi/.chezmoiexternals/ai-skills.toml.tmpl), [agent externals](../chezmoi/.chezmoiexternals/ai-agents.toml.tmpl), [filter](../python/skill_filter/skill_filter/main.py), [wrappers](../chezmoi/.chezmoiexternals/ai-authored-wrappers.toml.tmpl) |
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
Declare `<name> = "present"` in the [authored catalog](../chezmoi/.chezmoidata/ai/skills/authored.toml).
The [base externals](../chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl) and [overlay capability externals](../chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl) deploy nested authored skill files.
Only authored skill files with a final `.tmpl` suffix use template rendering; that suffix is removed from the output name.
Plain files keep their bytes, and both forms keep executable modes.
Source files that map to the same output path cause apply to fail.

The [file entry template](../chezmoi/.chezmoitemplates/ai/authored-file-entry) renders templates with the effective merged data from `.chezmoidata/` and `[data.*]` configuration.
Configuration values take precedence over catalog defaults at the same key path.
The [render context](../chezmoi/.chezmoitemplates/ai/authored-render-context) sets `chezmoi.sourceFile` to the canonical source path and `chezmoi.targetFile` to the rendered skill-relative or wrapper package-relative name.
Use `chezmoi.destDir` for destination paths and `dig` with safe defaults for optional data.
Use deterministic data; clocks, random values, and live lookups can change package versions on each apply.
The [base version template](../chezmoi/.chezmoitemplates/ai/authored-base-version) and [capability manifest](../chezmoi/.chezmoitemplates/ai/authored-plugin-manifest) calculate versions from rendered content, plain file hashes, executable modes, and selection data.

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
The [base cleanup hook](../chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-skills-cleanup.sh.tmpl) and [capability cleanup hook](../chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl) remove owned output with rendered names.
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

Declare each package under `[ai.plugin_bridge.capabilities.<name>]` in the capability catalog.
Set `source_dir` to its source directory under `src/overlay-plugins/`.
Skills use `<source_dir>/skills/` unless `skills_source_dir` names a separate skill root.
Set `wrapper_source_dir` to the canonical host package files and declare the supported `hosts`.
These paths start with `src/` and refer to the assembled tree.
Select skills under the capability's `skills` table with `"present"`, `"absent"`, or a declared host name.

```toml
[ai.plugin_bridge.capabilities.example]
description = "Example capability bundle."
source_dir = "src/overlay-plugins/example"
skills_source_dir = "src/overlay-skills"
wrapper_source_dir = "src/overlay-plugins/example/wrappers"
marketplace = "dotfiles"
hosts = ["claude", "codex", "cursor"]

[ai.plugin_bridge.capabilities.example.skills]
example = "present"
```

Put host files below `wrappers/claude/`, `wrappers/codex/`, and `wrappers/cursor/` for each declared host.
Use literal target names, such as `claude/.claude-plugin/plugin.json.tmpl` and `codex/.codex-plugin/plugin.json.tmpl`.
Only the final `.tmpl` suffix has special meaning; names such as `dot_claude-plugin` stay literal.
The [wrapper external](../chezmoi/.chezmoiexternals/ai-authored-wrappers.toml.tmpl) copies plain files, renders templates, and preserves executable modes through the existing [file entry template](../chezmoi/.chezmoitemplates/ai/authored-file-entry).
It uses the same chezmoi Go template engine and effective data as authored skills.
It places wrappers beside selected skills at `.local/share/agent-plugins/marketplace/plugins/<name>/<host>/` and copies Cursor packages to `.cursor/plugins/local/<name>/`.
Source-only files such as `AGENTS.md` and `README.md` at `source_dir` stay out of the package.
Only selected skill files and declared wrapper files enter these outputs.

The [wrapper inventory](../chezmoi/.chezmoitemplates/ai/authored-wrapper-files) rejects path escapes, symlinked sources, duplicate target paths, and wrappers that overlap `skills/`.
Host and environment gates prevent inactive wrapper templates from rendering.
Versions include rendered support files, executable modes, source-relative paths, and selection data.
The native `.<host>-plugin/plugin.json` manifest uses its raw source hash as a version input to prevent recursive version calculation.
The manifest itself still renders before delivery.
Pass `host` to the [manifest helper](../chezmoi/.chezmoitemplates/ai/authored-plugin-manifest) so packages with no skills for that host omit `./skills`.
If you omit `host`, the helper retains legacy behavior and includes `./skills` when any host has selected skills.
Cleanup records exact wrapper target paths and removes only previously recorded files, preserving unknown siblings.
Capabilities without `wrapper_source_dir` retain their existing native package files.

### Deselecting or removing skills

Set state to `"absent"` in the relevant catalog TOML file to deselect an authored or upstream skill.
Never delete catalog keys for removed skills, which leaves deployed files unmanaged.
`.chezmoiremove.tmpl` templates in each plugin host view and `dot_gemini/` tombstone and prune absent skills on `chezmoi apply`.

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
uv run pytest -p no:cacheprovider -m 'not integration' tests/integration/test_ai_skills.py tests/integration/test_ai_authored_capabilities.py tests/integration/test_ai_plugin_manifest_lifecycle.py tests/integration/test_ai_environment_fixtures.py tests/integration/test_overlay_authored_manifest_snapshot.py tests/integration/test_sbx_plugin_approval.py src/python/skill_filter/tests/
```
