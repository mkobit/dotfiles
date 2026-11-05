# SBX execution audit

## Environment

- Feature branch: `feat/sbx-rearch`, base `7aa2fb19`.
- Host and guest workdir: `/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch`.
- Environment: `.sbx/sbxenv.yaml`, sandbox name `dotfiles-sbx-rearch`.
- Kit: `.sbx/kit/spec.yaml`, setup `.sbx/kit/install.sh`.
- Mount: direct, `clone: false`; guest Git metadata is unavailable for this host worktree.
- Git, signing, commits, and publication stay on the host for this migration.
- Config task brief: `.sbx/task-context/config-task.md`; task context and logs are ignored.
- No writer launched by this audit agent.

## Evidence

- `sbx version`: v0.50.1, exit 0.
- Restricted `sbx diagnose --format json`: exit 1, socket operation denied, state read-only.
- Escalated retry: exit 0, 16 pass, 0 fail, 2 expected skips.
- `sbx kit validate .sbx/kit`: exit 0 for the minimal kit before toolchain expansion.
- `sbx env plan .sbx/sbxenv.yaml`: exit 0; new sandbox and local kit, no destroys.
- `sbx env create --force .sbx/sbxenv.yaml`: exit 0; dedicated environment created.
- Guest executable: `/home/agent/.local/bin/codex`, version 0.165.0.
- Guest provider: sandboxd; model and effort unspecified in config.
- Worker launch must explicitly set `--model gpt-6.1-sol -c model_reasoning_effort=high`.
- Verified flags: `--disable hooks`, `--dangerously-bypass-approvals-and-sandbox`, `--skip-git-repo-check`, `-C`, `-o`, `--json`.
- Initial guest tools: uv0.13.5, Python3.14.4; no mise or chezmoi.
- Pinned setup uses npm for mise2026.10.23 and mise for locked uv0.12.10, chezmoi2.74.0, Python3.14.7.
- No custom curl/wget binary downloads remain in the tracked kit.
- Tool install is running through `sbx env exec`; no sandbox restart or replacement.

## Command

Run from the feature worktree with required platform access:

```sh
sbx env exec --name dotfiles-sbx-rearch .sbx/sbxenv.yaml -- /home/agent/.local/bin/codex exec --model gpt-6.1-sol -c model_reasoning_effort=high --disable hooks --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C /home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch 'Read .sbx/task-context/config-task.md and perform the assigned task.'
```

## Design corrections

- Guest commits need a full checkout or clone, not a host worktree with external Git metadata.
- AGY uses tracked `agent: antigravity` contrib kit; it is not a built-in `agy` agent.
- Model flags require both experimental-features and feature.model opt-in.
- Local policy initialization is one-time; preserve existing rules.
- Skill import follows top-level symlinks, skips nested symlinks, and replaces whole skills.
- Disabled source skills can leave old store copies.
- SSH signing needs a forwarded socket and an available public key.
- GPG subkey transport remains unverified.

Sources: [Git workflows](https://docs.docker.com/ai/sandboxes/workflows/git/), [CLI authentication](https://docs.docker.com/ai/sandboxes/workflows/authentication/), [Models](https://docs.docker.com/ai/sandboxes/configuration/models/), [Skills](https://docs.docker.com/ai/sandboxes/workflows/agent-skills/), [Mise installation](https://mise.jdx.dev/installing-mise.html).

## Final tool readiness

- Pinned tool setup passed after repair.
- Mise: `/home/agent/.local/bin/mise`, 2026.10.23.
- Chezmoi: `/home/agent/.local/bin/chezmoi`, 2.74.0.
- Python: `/home/agent/.local/bin/python3`, 3.14.7.
- `mise exec -- uv --version`: 0.12.10.
- Set `UV_PROJECT_ENVIRONMENT=/home/agent/.local/share/dotfiles/venv` for guest dependencies; do not reuse the host `.venv`.
- Initial setup attempts exited 1 because global chezmoi/Python selections conflicted with root `locked=true`.
- Repair installs those exact tools from `/home/agent` without adding global selections and exposes binaries in the guest local bin directory.
- No repository lockfile change and no minimum-release-age bypass.
- Restricted kit inspect/validate calls also ended with a misleading login-store lock error; escalated calls passed.
- Runtime uses manual tracked `install.sh` execution for this existing environment. Future environment creation runs the same script as a kit install step.
- No sandbox restart or replacement was used.

## Final checks

- Final `sbx kit validate .sbx/kit`: exit 0.
- Final guest `sh -n .sbx/kit/install.sh`, uv/chezmoi/Python version checks, and brief existence check: exit 0.
- Host `git diff --check`: exit 0.
- Host `git check-ignore` confirms task context and log artifacts are ignored.
- No audit processes remain active.

## Review repair: uv Python selection

- Reproduced `mise exec -- uv python find --no-python-downloads`: exit 2; project `python-preference = only-managed` excludes the mise interpreter.
- `UV_PYTHON` alone still produced exit 2 for `uv python find`.
- Added tracked `UV_PYTHON=/home/agent/.local/share/mise/installs/python/3.14.7/bin/python3` and `UV_PYTHON_PREFERENCE=system` to kit environment.
- Added a setup check with the same explicit interpreter settings.
- With both variables, `mise exec -- uv python find --no-python-downloads`: exit 0, `/home/agent/.local/bin/python3` (symlink to the pinned interpreter).
- `UV_PROJECT_ENVIRONMENT=/home/agent/.local/share/dotfiles/uv-python-check mise exec -- uv run --no-sync --no-python-downloads python -c 'import sys; assert sys.version_info[:3] == (3, 14, 7); print(sys.executable); print(sys.version)'`: exit 0; independent guest venv uses Python3.14.7.
- The tracked kit variables describe future creation. This running environment predates the final kit and still requires explicit `UV_PROJECT_ENVIRONMENT`, `UV_PYTHON`, `UV_PYTHON_PREFERENCE`, and `MISE_MINIMUM_RELEASE_AGE` in launch/check commands.
- No dependency sync, active-worker venv access, restart, or environment replacement occurred.

## Review repair: uv package age

- Added `UV_EXCLUDE_NEWER=P7D` to kit variables and install script; host uv config is not mounted.
- Live checks pass the package age and interpreter variables explicitly because the environment predates the final kit.
- Final kit validation, setup shell syntax, uv interpreter lookup, and isolated uv run checks pass with all runtime settings.
- The isolated run asserts Python3.14.7 and `UV_EXCLUDE_NEWER=P7D`; it performs no dependency resolution or sync.
