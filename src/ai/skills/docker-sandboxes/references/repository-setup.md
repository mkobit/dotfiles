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

1. Run `sbx kit validate .sbx/kit`.
2. Run `sbx env plan .sbx/sbxenv.yaml`.
3. Run `sbx env create .sbx/sbxenv.yaml`.
4. Run checks or an agent session in the environment.
5. Review changes and perform Git delivery on the host.
6. Run `sbx env rm .sbx/sbxenv.yaml --force` when the environment is no longer needed.
