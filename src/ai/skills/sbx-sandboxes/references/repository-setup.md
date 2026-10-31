# Repository setup

Each consuming repository owns a complete, tracked `.sbx/` setup.

The repository provides its own runtime, toolchain, packages, ports, services, and kit behavior.

## Minimal layout

- `.sbx/sbxenv.yaml` defines the primary environment.
- `.sbx/kit/spec.yaml` defines the repository toolchain kit.
- `.sbx/sbxenv.agy.yaml` is optional when the repository supports AGY.

## Environment template

Use this baseline for a Codex environment.

```yaml
schemaVersion: "1"
name: "<project-slug>-codex"
agent: codex
workspace:
  path: ..
  clone: false
kits:
  - ./kit
```

Add `ports` only for repository services that require them.
Declare only `sandbox` ports and omit `host`; see [Environment files](environment-files.md#ports).

`clone: false` is the default because the sandbox directly mounts the checkout and changes return to the host immediately.

Use `clone: true` only when a private in-VM clone is required and the repository documents how the host receives reviewed changes.

## Kit baseline

Start `.sbx/kit/spec.yaml` as an SBX mixin.

```yaml
schemaVersion: "2"
kind: mixin
name: <project-slug>-toolchain
version: "0.1.0"
description: Bootstrap the project toolchain
```

Add only the runtime and setup needed by the repository.

Declare every package and runtime download domain in the kit network policy.

Keep kit commands reproducible from repository-tracked toolchain files.

## Lifecycle

Use the approved task authority for needed task-specific setup without another confirmation solely for setup.
Keep actual platform permissions in effect and do not perform unrelated destructive changes.
Use the [workspace contract](../../sbx-orchestrator/references/nested-execution.md#workspace-ownership) for branch, worktree, write boundaries, and ownership.

Use this procedure only when the environment is missing or its configuration changed.
For an existing environment with unchanged configuration and verified readiness, use `sbx env exec` without repeating setup.

Inspect `sbx ls --format json` if the environment state is unknown.
Validate and plan the required setup:

```sh
sbx kit validate .sbx/kit
sbx env plan .sbx/sbxenv.yaml
```

Create a missing environment with `sbx env create .sbx/sbxenv.yaml` when the approved task needs it.
For changed configuration, use the plan to identify the required update or rebuild.
Keep authorized environment removal separate from task execution.

Run checks in the environment and review any direct-mounted changes on the host.

Perform Git delivery on the host when authorized.

Remove the environment only when authorized.

## Environment readiness

Before concurrent launches, prove one representative environment with direct checks.
Record the effective sandbox name, environment configuration, mount mapping, and absolute guest workdir.
Verify the installed harness executable and help, runtime tools, locked dependencies, Git context, and [read-only task context](../../sbx-orchestrator/references/subagent-task.md#read-only-task-context).
Run required tools, such as `mise --version` and `bun --version`, and the repository's dependency check.
An installer exit of zero does not prove those tools work.
Use the verified absolute executable when `PATH` lookup fails.
Separate a stopped environment, missing `PATH` entry, absent executable, host restriction, and authentication failure.
Use [permissions](permissions.md) for host restrictions and [authentication](authentication.md) for sign-in failures.

A worktree's Git metadata can be outside the mount.
Record what the guest can read and use host-verified base evidence and supported harness flags as described in [worker launch](../../sbx-orchestrator/references/worker-launch.md).
Do not mount host Git metadata or credentials to bypass this boundary.
Preserve readiness evidence and reuse it until relevant configuration changes or a failure requires a new check.
Check each assigned mount and workdir against that evidence before dispatch.
Report missing prerequisites; do not infer readiness from environment existence.

## CI scope

Follow each consuming repository's CI policy; this skill does not require runtime SBX execution in CI.
Storagemaxxing SBX CI is limited to offline kit validation and static environment validation.
Do not add Docker credentials, sign-in, daemon setup, provisioning, guest execution, or runtime cleanup to that CI.
This restriction does not remove the repository's existing application CI checks.
