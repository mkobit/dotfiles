---
name: docker-sandboxes
description: Use when configuring a repository-owned `.sbx/` environment or kit, or when coordinating host builds, tests, and delegated agents through `sbx env`.
allowed-tools:
  - Bash(sbx ls --format json)
  - Bash(sbx kit validate .sbx/kit)
  - Bash(sbx env plan .sbx/sbxenv.yaml)
  - Bash(sbx env exec .sbx/sbxenv.yaml -- *)
---

# Docker Sandboxes

Use this skill to run repository work through `sbx env` or configure a repository-owned `.sbx/` environment.

Keep host credentials, Git review, commits, signing, and pushes on the host.
Each repository owns its `.sbx/` configuration, including its kit, runtime, toolchain, packages, ports, and services.

## Default workflow

**Reuse → execute → review → report.**

For an existing environment with unchanged configuration, dispatch immediately.
Validate, create, or rebuild only when the environment is missing or its configuration changed; use [Repository setup](references/repository-setup.md).

“Do this task in SBX” authorizes file edits and required checks within the task scope.
Do not add read-only restrictions or another routine approval step.

1. Select and claim a bead that can finish in one repository.
2. Supply its context, file scope, acceptance criteria, and required checks, then dispatch to the existing environment with the [Codex example](references/agents.md#codex-execution).
3. Review the diff and check results on the host.
4. Update the bead on the host and return a short result with the log location.

Choose a bounded implementation task over a broad design or cross-repository workflow task, even if the broader task has higher priority.
Keep Beads writes and publication on the host.
Save detailed output in task logs.
Run required checks once; repeat them only after relevant changes or failures.

Use `workspace.clone: false` so sandbox edits are immediately visible to the host.
For private clones and the change-return process, read [Nested execution](references/nested-execution.md).

Read [Permissions](references/permissions.md) before requesting an escalated command or configuring command grants.
Read [CLI automation](references/cli-automation.md) for v0.48 command behavior.

## References

- [Repository setup](references/repository-setup.md) describes a repository-owned `./kit` and environment file.
- [Environment files](references/environment-files.md) covers workspace and lifecycle choices.
- [Nested execution](references/nested-execution.md) covers coordinator-to-sandbox delegation.
- [Agents](references/agents.md) covers Codex, Claude, and AGY harnesses.
- [Upstream pins](references/upstream-pins.md) records the AGY kit pin.
- [CLI automation](references/cli-automation.md) covers machine-readable output, prompts, and lifecycle behavior.
