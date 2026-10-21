# AI skill and plugin architecture

## Architecture overview

manages all skill and plugin assets through Chezmoi under `.chezmoiroot`.
deploys portable skills to `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills/`.
deploys host views to `claude/`, `codex/`, and `cursor/` subdirectories under `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/`.
chezmoi generates marketplace manifests from the catalog through the shared `ai/plugin-marketplace` template.
runs post-apply bridge script `run_after_agent-plugin-bridge.sh.tmpl` calling `src/python/skill_filter/skill_filter/plugin_bridge.py` to register marketplaces and plugins in Claude Code and OpenAI Codex.
Antigravity consumes direct flat skills under `~/.gemini/antigravity-cli/skills/` and discovers plugin bundles via declarative `~/.gemini/config/plugins.json` pointing to the dotfiles and enabled Superpowers package parent directories.
Antigravity skill deployment and configuration are gated on `local.bin.agy.installation_method != 'none'`, allowing work overlays to omit Antigravity entirely.
OpenCode V1 receives local package paths in `~/.config/opencode/opencode.json` only when its existing tool gate and the plugin package gate are enabled.

## Workflows for AI agents

### Authored skills

create `src/ai/skills/<name>/SKILL.md` for authored skill content.
declare `<name> = "present"` in `src/chezmoi/.chezmoidata/ai/skills/authored.toml`.
nested files under `src/ai/skills/<name>/` deploy automatically via `src/chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl`.

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
its shared root is `.local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers/`.
Claude Code and Codex register it as `superpowers@superpowers-marketplace`, separate from `mkobit-dotfiles@dotfiles`.
each generated marketplace declares its destination-relative `source_locator`, owner, source, trust class, and native hosts in the keyed marketplace catalog.
`plugin_declarations.py` validates and plans declarations without file writes.
each marketplace has one source template per native host, which calls the shared renderer.
overlays can add marketplace templates and catalog declarations through the same structure.
provenance reports each capability's marketplace, source, and trust class from its own declaration.
Cursor receives an identical archive at `.cursor/plugins/local/superpowers/` and uses the upstream manifest and hooks there.
the [upstream OpenCode adapter](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/.opencode/INSTALL.md) uses the shared root as an absolute local package directory in the pinned V1 `plugin` array.
OpenCode registration also requires `local.bin.opencode.installation_method != "none"`.
OpenCode retires only the old managed Superpowers package reference and preserves unrelated plugin entries.
Antigravity adds the enabled Superpowers package parent directory and keeps its existing dotfiles registration and tool gate.
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
