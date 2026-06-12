# AI skill deployment

Skills deploy as static files via chezmoi externals — never the Claude plugin marketplace or `claude plugin` CLI.
The catalog is `src/chezmoi/.chezmoidata/ai/skills.toml`: upstream sources pin a commit `ref` + archive `sha256`; skill entries are `"present"` (all tools), `"absent"`, or a single tool name like `"claude"` (never delete a key — set it `"absent"` so `.chezmoiremove.tmpl` prunes the installed copy).
Authored skills live in `src/ai/skills/<name>/` and deploy as copies, never symlinks.
Upstream Claude Code subagents use the same model via `.chezmoidata/ai/agents.toml` (Claude-only — agent frontmatter is tool-proprietary); onboarding any upstream skill or agent requires a content review at the pinned ref.
`src/python/skill_filter` must stay stdlib-only — it runs via system python3 at apply time, before uv/mise exist.
Guide: `README.md` in this directory.
