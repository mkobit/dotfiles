# Configuration interface

Task 2 declares capabilities in `src/chezmoi/.chezmoidata/ai/workflow.toml`.
Personal decisions belong in `src/chezmoi/.chezmoi.toml.tmpl`.
An overlay can omit each decision.
Consumers must use `dig` with the defaults below.

| Data path | Missing value | Meaning |
| --- | --- | --- |
| `ai.workflow.enabled` | `false` | Enable global workflow tasks. |
| `ai.sandbox.provider` | `"none"` | Select `sbx` or disable setup. |
| `ai.sandbox.default_clone_mode` | `false` | Select the default workspace mode. |
| `ai.sandbox.network_policy` | `""` | Opt in to initial `balanced` policy when no policy exists. |
| `ai.sandbox.proxy_gh_secret` | `false` | Configure the `github` host resolver. |
| `ai.sandbox.sync_skills` | `false` | Import selected authored portable skills. |
| `sbx.settings.skills_default_mode` | `""` | Opt in to `readonly`, `readwrite`, or `off`. |
| `ai.signing.mode` | `"host-default"` | Select `ssh-forwarded`, `gpg-subkey`, or existing settings. |
| `ai.signing.ssh_public_key` | `""` | Explicit public key; empty requires a guest signing proof with existing config. |
| `ai.signing.gpg_subkey_id` | `""` | Explicit GPG signing subkey; empty is an unmet prerequisite. |
| `ai.ollama.enabled` | `false` | Enable local model routes and experimental features. |
| `ai.ollama.host_url` | `""` | Explicit host route. |
| `ai.ollama.sandbox_url` | `""` | Explicit guest route. |
| `ai.ollama.default_coder_model` | `""` | Explicit model selection. |

Keep `ai.skills.authored` and `ai.command_policy.commands` as existing maps.
Do not add a duplicate `ai.sandbox.skills_mode` value.
Do not change existing `sbx.settings.kit_allowed_sources` semantics.

Task 3 uses ordinary apply hooks `run_after_06_configure-sbx-workflow.sh.tmpl` and `run_after_07_sync-sbx-skills.sh.tmpl`.
Its tests are `test_sbx_workflow_setup.py` and `test_sbx_skill_sync.py`.
See [the setup report](setup-report.md).
Task 7 owns guest signing preflight and configuration; task 3 does not prove guest signing.

Use the existing portable source at `.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills` under `chezmoi.destDir`.
Do not modify plugin caches.
If SBX cannot import this source directly, stage only task-owned files with an ownership check.
Report unsupported removal behavior.

Task 6 uses [the model route contract](model-routing.md).
Task 7 uses [the corrected task contract](task7-refinement.md) and [guest task transport](guest-task-contract.md).
Its helper, runtime projection, assignment snapshot, state, and exact-head review acceptance share one saved run identity.
The tracked kit supplies the static task wrapper; the host supplies explicit run assets.
Host state retains tracker authority, the frozen assignment, review acceptance, and close evidence.
Guest state cannot select a new tracker or authorize host close.
