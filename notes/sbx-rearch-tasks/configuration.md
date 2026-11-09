# Configuration task

Workspace: /home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch
Branch: feat/sbx-rearch
Base: 34409dd3
Spec: notes/sbx-rearch.md
Plan: notes/sbx-rearch-plan.md

Implement plan tasks 2 and 3, then 6 as separate verified units.
You own only the following areas: new workflow data under src/chezmoi/.chezmoidata/ai/, personal opt-ins in src/chezmoi/.chezmoi.toml.tmpl, existing/new SBX settings scripts, OpenCode/Pi model modifier files, and focused integration test files for this work.
Do not modify command_policy, skills/authored.toml, or skill sources; another unit owns these.
You are not alone in the codebase; preserve others' edits.
Do not spawn agents, commit, push, change credentials, or change host policy.

Read applicable AGENTS.md, existing SBX settings and integration tests first.
Use existing map interfaces and modifier conventions.
Keep installation decisions in the init control plane, with safe dig defaults when an overlay omits decisions.
Propose the exact paths in /tmp/sbx-rearch-config-interface.md before implementation so root can give them to consumers.
Use ai.sandbox, ai.signing, ai.ollama to match the conceptual spec; keep ai.skills.authored and ai.command_policy as existing maps. Use ai.workflow.enabled to gate global tasks. Keep skills mode at sbx.settings.skills_default_mode. Missing signing mode is host-default. Empty SSH key permits an existing configured signing key only when guest preflight proves signing works.
Schema catalogs describe capabilities, not enabled personal decisions.

Requirements:
1. Personal SBX workflow opts in through the control plane. Overlay absence or disabled provider renders no setup.
2. Preserve existing kit_allowed_sources behavior. Settings scripts compare before setting, work without TTY, and report unavailable SBX as skipped.
3. Preserve custom network policy; initialize balanced only when no policy exists, using actual supported inspection commands.
4. Configure readonly skills and secret resolver gh auth token only when explicitly opted in. Never print tokens or mint keys.
5. Signing configuration must select an explicit SSH public key or GPG subkey; missing key is an unmet prerequisite. Do not auto-select first agent key or export private keys. Keep host signing settings intact. Guest signing preparation may be a task-consumable config rather than host global git mutation.
6. Import real authored portable skill files without modifying plugin caches. Inspect actual sbx import source support; stage owned files under an import source only with safe ownership semantics. Cover disabled/removed skills if possible; clearly record unavailable store-removal semantics.
7. Ollama: explicitly gated host/sandbox URL and model settings, preserve unrelated OpenCode/Pi settings. Verify current native Pi path/schema from official source. Enable both required experimental/model flags only on explicit opt-in and preserve existing providers.
8. Tests first for executable behavior, red then green. Use fake sbx and chezmoi render patterns. Test missing decisions, disabled features, overlay overrides, idempotence, service failures, existing policy, preserving live fields, and paths under isolated destDir.
9. Keep dependencies unchanged and use mise entry points (mise exec -- uv run ... until verify exists).
10. Record unsupported/manual items honestly; do not silently call work complete.

Return short status plus changed files and checks/exit codes. Write full report to /tmp/sbx-rearch-config-report.md. Separate each logical unit in report so root can commit it before next unit. Stop after tasks 2/3 first and report; wait for root before task 6.
