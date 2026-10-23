# AI skill and plugin architecture

## Architecture overview

manages all skill and plugin assets through Chezmoi under `.chezmoiroot`.
deploys portable skills to `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills/`.
deploys host views to `claude/`, `codex/`, and `cursor/` subdirectories under `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/`.
runs post-apply bridge script `run_after_agent-plugin-bridge.sh.tmpl` calling `src/python/skill_filter/skill_filter/plugin_bridge.py` to register marketplaces and plugins in Claude Code and OpenAI Codex.
Antigravity consumes direct flat skills under `~/.gemini/antigravity-cli/skills/` and discovers plugin bundles via declarative `~/.gemini/config/plugins.json` pointing to `.local/share/agent-plugins/marketplace/plugins`.
Antigravity skill deployment and configuration are gated on `local.bin.agy.installation_method != 'none'`, allowing work overlays to omit Antigravity entirely.
OpenCode V1 receives local package paths in `~/.config/opencode/opencode.json` only when its existing tool gate and the plugin package gate are enabled.

## Workflows for AI agents

### Authored skills

create `src/ai/skills/<name>/SKILL.md` for plain authored skill content, or `SKILL.md.tmpl` to use chezmoi Go templates.
declare `<name> = "present"` in the [authored catalog](../chezmoi/.chezmoidata/ai/skills/authored.toml).
the [base externals](../chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl) and [overlay capability externals](../chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl) deploy nested authored skill files.
only authored skill files with a final `.tmpl` suffix use template rendering; that suffix is removed from the output name.
plain files keep their bytes, and both forms keep executable modes.
source files that map to the same output path cause apply to fail.

the [file entry template](../chezmoi/.chezmoitemplates/ai/authored-file-entry) renders templates with the effective merged data from `.chezmoidata/` and `[data.*]` configuration.
configuration values take precedence over catalog defaults at the same key path.
the [render context](../chezmoi/.chezmoitemplates/ai/authored-render-context) sets `chezmoi.sourceFile` to the canonical source path and `chezmoi.targetFile` to the rendered skill-relative name.
use `chezmoi.destDir` for destination paths and `dig` with safe defaults for optional data.
use deterministic data; clocks, random values, and live lookups can change package versions on each apply.
the [base version template](../chezmoi/.chezmoitemplates/ai/authored-base-version) and [capability manifest](../chezmoi/.chezmoitemplates/ai/authored-plugin-manifest) calculate versions from rendered content, plain file hashes, executable modes, and selection data.

the [technical-writing template](skills/technical-writing/SKILL.md.tmpl) accepts optional `ai.skills.content.technical-writing.description` and `ai.skills.content.technical-writing.instructions` strings.
a non-empty description replaces the YAML description with a quoted scalar.
non-empty instructions follow the unchanged Markdown body after a blank line.
missing or empty values keep the original description and body bytes.
catalog defaults use `[ai.skills.content.technical-writing]`; an overlay can override either value in its init template:

```toml
[data.ai.skills.content.technical-writing]
description = "Use when writing standalone documentation."
instructions = "Follow the project style guide."
```

rendered output uses the existing portable, host, Cursor local, and gated Antigravity paths described above.
the [base cleanup hook](../chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-skills-cleanup.sh.tmpl) and [capability cleanup hook](../chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl) remove owned output with rendered names.
the [plugin bridge](../python/skill_filter/skill_filter/plugin_bridge.py) registers the generated packages after apply.
rendering leaves canonical sources unchanged; edit those sources, not deployed copies.
third-party packages, host conversion, and native package registration keep their existing behavior.

### Upstream third-party skills

pin `repo`, `ref`, and `sha256` under `[ai.skills.external.<source>]` in `src/chezmoi/.chezmoidata/ai/skills/<source>.toml`.
select individual skills under `[ai.skills.external.<source>.skills]` with state `"present"` or a specific host name (`"claude"`, `"codex"`, `"cursor"`, `"antigravity"`).

```toml
[ai.skills.external.example]
repo = "<owner>/<repo>"
ref = "<full commit sha>"
sha256 = "<sha256 of downloaded archive>"

[ai.skills.external.example.skills]
example = "present"
```

compute the pin for a new commit with `curl`:

```sh
curl -sL https://codeload.github.com/<owner>/<repo>/tar.gz/<commit-sha> | sha256sum
```

set `skill_file = "SKILL.md"` on single-skill repositories shipping `SKILL.md` at archive root instead of under `skills_root/<name>/`.

### Internal GitHub Enterprise or corporate proxy

declare a custom archive host under `[ai.skills.hosts.<host>]` in `src/chezmoi/.chezmoidata/ai/hosts.toml` or in an overlay using `url_format` with `{repo}` and `{ref}` tokens.
set explicit `url` on a source table under `[ai.skills.external.<source>]` for one-off published archives.

```toml
[ai.skills.hosts.ghe]
url_format = "https://ghe.internal/api/v3/repos/{repo}/tarball/{ref}"
```

### Overlay-authored skills

set `ai.skills.overlay_authored_source` in overlay configuration to point to a local directory of skills.
declare skill names under `[ai.skills.authored]` in the overlay catalog with state `"present"` or a specific host name.
skills present in the overlay source directory take precedence over base authored skills with identical names.

### Dividing into plugins or capabilities

declare capability bundles under `[ai.plugin_bridge.capabilities.<name>]` in `src/chezmoi/.chezmoidata/ai/plugin-bridge.toml`.
set `marketplace = "dotfiles"` and specify target host list under `hosts`.

```toml
[ai.plugin_bridge.capabilities.mkobit-dotfiles]
description = "Base dotfiles capability bundle."
acquisition_destination = true
marketplace = "dotfiles"
hosts = ["claude", "codex", "cursor"]
```

### Deselecting or removing skills

set state to `"absent"` in the relevant catalog TOML file to deselect an authored or upstream skill.
never delete catalog keys for removed skills, which leaves deployed files unmanaged.
`.chezmoiremove.tmpl` templates in each plugin host view and `dot_gemini/` tombstone and prune absent skills on `chezmoi apply`.

## Upstream plugin packages

declare archive metadata under `[ai.plugins.<name>]` in `src/chezmoi/.chezmoidata/ai/plugins/<name>.toml`.
enable the package in the init template:

```toml
[data.ai.plugins.superpowers]
installation_method = "chezmoi_external"
```

set the method to `"none"` to remove the managed package and its host registrations.
a missing method also means `"none"`.
the archive pin uses a full commit ref and archive SHA-256.
archive hosts use the existing `ai.skills.hosts` catalog, so an overlay can select its package mirror.

[Superpowers v7.0.0](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3) deploys the complete repository, with no skill filter or workflow edits.
its shared root is `.local/share/agent-plugins/marketplace/plugins/superpowers/`.
Claude Code and Codex register that root through the local marketplace bridge.
Cursor receives an identical archive at `.cursor/plugins/local/superpowers/` and uses the upstream manifest and hooks there.
the [upstream OpenCode adapter](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/.opencode/INSTALL.md) uses the shared root as an absolute local package directory in the pinned V1 `plugin` array.
OpenCode registration also requires `local.bin.opencode.installation_method != "none"`.
Antigravity keeps its existing parent-directory registration and tool gate.
Gemini CLI stays disabled where its tool gate is absent or set to `"none"`.
the package retains upstream rules, agents, hooks, and runtime helpers.
legacy per-skill Superpowers selections stay `"absent"` so apply removes duplicate copies.

## Upstream agents

agents follow the pin-and-select model via `src/chezmoi/.chezmoidata/ai/agents.toml` and `src/chezmoi/.chezmoiexternals/ai-agents.toml.tmpl`.
Claude Code receives raw markdown files under `~/.claude/agents/<source>/`.
Antigravity and Cursor consume agents rewritten to `SKILL.md` format by `skill_filter`.
OpenCode receives agents under `~/.config/opencode/agents/<source>/` rewritten with explicit `name` and `mode: subagent`.
onboarding an agent requires a prompt-injection review of content at the pinned ref.

## Verification and testing

preview pending changes:

```sh
chezmoi diff
```

apply skill and plugin updates:

```sh
chezmoi apply
```

run test suite and linters:

```sh
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest tests/integration/test_ai_skills.py tests/integration/test_ai_environment_fixtures.py tests/integration/test_opencode_plugins.py
```
