# Repository setup

Create `.sbx/.sbxenv.yaml` from `templates/codex.sbxenv.yaml` after replacing `{{PROJECT_SLUG}}` with a stable repository-safe name.

Create `.sbx/.sbxenv.agy.yaml` from `templates/agy.sbxenv.yaml` only when the user wants AGY.

Add `.sbx/local.sbxenv.yaml` to the repository’s `.gitignore` before creating a host-specific overlay.

The Codex environment is run with `sbx env run .sbx`.

The AGY environment is run with `sbx env run .sbx/.sbxenv.agy.yaml`.

Use `sbx env create` for non-interactive provisioning and `sbx env exec` for explicit checks.

Keep separate names for each agent because each environment has its own VM, clone, state, and sandbox Git remote.

Do not add a repository kit by default.

Create `.sbx/kit/` only when the inspected repository needs repeatable project-specific setup that cannot be expressed by its checked-in tooling.

Make a shared mise or skills mixin only after the same reviewed setup is needed by multiple repositories.
