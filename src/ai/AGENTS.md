# AI skill deployment

Chezmoi owns plugin archives, version pins, and skill assets.
The plugin bridge registers local marketplaces and unchanged upstream packages with each supported host.
Full upstream plugin metadata lives in `src/chezmoi/.chezmoidata/ai/plugins/*.toml`.
The init template enables each package with `[data.ai.plugins.<name>] installation_method = "chezmoi_external"`; a missing method means `"none"`.
Keep upstream plugin files unchanged, including skills, hooks, agents, rules, and runtime helpers.
Antigravity also receives direct skill copies.
The catalog is `src/chezmoi/.chezmoidata/ai/skills/*.toml`, with archive hosts in `src/chezmoi/.chezmoidata/ai/hosts.toml`: upstream sources pin a commit `ref` + archive `sha256`; skill entries are `"present"` (all tools), `"absent"`, or a single tool name like `"claude"` (never delete a key — set it `"absent"` so `.chezmoiremove.tmpl` prunes the installed copy).
Authored skills live in `src/ai/skills/<name>/` and deploy as copies inside owned plugin bundles, never symlinks.
Upstream agents use the same model via `.chezmoidata/ai/agents.toml`: Claude Code gets the raw format under `~/.claude/agents/<source>/`, antigravity and cursor receive each agent rewritten as a skill by the `skill_filter` `agent-skill` transform, and opencode gets agents rewritten by `agent-opencode` under `~/.config/opencode/agents/<source>/`; onboarding any upstream skill or agent requires a content review at the pinned ref.
`src/python/skill_filter` must stay stdlib-only — it runs via system python3 at apply time, before uv/mise exist.
Guide: `README.md` in this directory.
