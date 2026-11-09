# AI skill deployment

Chezmoi owns plugin archives, version pins, and skill assets.
The plugin bridge registers local marketplaces and unchanged upstream packages with each supported host.
Full upstream plugin metadata lives in `src/chezmoi/.chezmoidata/ai/plugins/*.toml`.
The init template enables each upstream package with `[data.ai.plugins.<name>] installation_method = "chezmoi_external"`; a missing method means `"none"`.
Keep upstream plugin files unchanged, including skills, hooks, agents, rules, and runtime helpers.
Antigravity also receives direct copies of upstream skills.
The catalog is `src/chezmoi/.chezmoidata/ai/skills/*.toml`, with archive hosts in `src/chezmoi/.chezmoidata/ai/hosts.toml`: upstream sources pin a commit `ref` + archive `sha256`; skill entries are `"present"` (all tools), `"absent"`, or a single tool name like `"claude"` (set a deselected entry to `"absent"` so the host `.chezmoiremove.tmpl` prunes copies, then delete the key after about two months; machines that apply later clean leftovers by hand).
Authored plugins are native chezmoi folders under `src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_<name>/`, with identity in `.chezmoidata/ai/plugins/<name>.toml`; base skills live in `exact_mkobit-dotfiles/exact_skills/exact_<skill>/`.
Keep the three layers apart: generation templates write files only, externals bring third-party content, and the `run_after` bridge installs through host CLIs without writing package files.
Upstream agents use the same model via `.chezmoidata/ai/agents.toml`: Claude Code gets the raw format under `~/.claude/agents/<source>/`, antigravity and cursor receive each agent rewritten as a skill by the `skill_filter` `agent-skill` transform, and opencode gets agents rewritten by `agent-opencode` under `~/.config/opencode/agents/<source>/`; onboarding any upstream skill or agent requires a content review at the pinned ref.
`src/python/skill_filter` must stay stdlib-only — it runs via system python3 at apply time, before uv/mise exist.
Guide: `README.md` in this directory.
