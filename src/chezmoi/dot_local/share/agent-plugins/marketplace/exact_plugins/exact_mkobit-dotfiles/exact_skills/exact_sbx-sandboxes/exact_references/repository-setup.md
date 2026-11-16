# Repository setup

Each repository owns its tracked `.sbx/` environment, kit, tools, services, and checks.
Read its project instructions, latest-state records, and delegation rules first.
Do not initialize a tracker to discover the task.

## One complete task

A person or an agent can use [repository bootstrap](../../repo-bootstrap/SKILL.md) with the same task description.
Record scope and exclusions, branch and base commit, required checks, action authority, and return location.
Use exact paths for the environment, guest workdir, report, and change return.
For a worker, use the installed [SBX orchestrator](../../sbx-orchestrator/SKILL.md) for launch, progress, and recovery.
For a command-only request, use native `sbx env exec`; do not launch a coding worker.
No extra repository task helper is required.

The default task permits edits and checks only.
The host coordinator retains Git delivery, signing, publishing, and tracker authority.
An explicit private-clone assignment can transfer the named actions to the guest worker.
This assignment must state the permitted commits, remote and branch, PR actions, signing identity, and tracker actions as applicable.
Do not infer this authority from credentials, a tool grant, or an approval bypass flag.
Keep actual platform permissions in effect.
Ask only for missing authority, a required credential action, a scope increase, or an unrelated destructive change.

## Native kit composition

Use a pinned native v3 workload with a repository-owned v3 tool mixin.
Keep the workload's native agent launch command.
The [kit guide](https://docs.docker.com/ai/sandboxes/customize/use-kits/) and [tool mixin guide](https://docs.docker.com/ai/sandboxes/customize/author/tool-mixins/) define the native formats.

The repository owns these files:

- `.sbx/sbxenv.yaml` selects the workload, mixin, and workspace mode.
- `.sbx/kit/spec.yaml` declares the v3 mixin and its capabilities.
- `.sbx/kit/Dockerfile` packages any repository installation code in the kit.

For example, this repository uses the following composition:

```yaml
schemaVersion: "1"
name: dotfiles-private-guest
agent: sbx-kit-codex
workspace:
  path: ..
  clone: true
kits:
  - docker.io/docker/sbx-kit-codex@sha256:f808ef79b5aae10dcfd896dc898e16cbfd806bcd16c9699d208ccb99001eaf76
  - ./kit
```

Use the repository's reviewed workload pin rather than selecting an unreviewed latest image.
For direct-mounted tasks, keep their existing agent selection and `clone: false` default.
Do not change unrelated environment modes to run a private-clone task.
Add only required service ports; see [environment files](environment-files.md#ports).

A v3 mixin starts with this source format:

```yaml
# syntax=docker/sandbox-kit:3
schemaVersion: "3"
kind: mixin
displayName: Project toolchain
version: "0.1.0"
description: Install the project tools and frozen dependencies
dockerfile: Dockerfile
```

Add native network-policy and lifecycle capabilities for the repository.
Declare package and runtime download domains in the kit network policy.
Package installation code in the kit; do not depend on a host-only helper path.
Use install lifecycle commands to install system tools, trust the project mise configuration, install pinned tools, and prepare frozen dependencies.
Run project setup in the assigned workspace with the intended guest user.
Keep lockfiles, release ages, and binary checksums unchanged unless the task assigns their update.
Do not move these operations into the task prompt or require manual `mise trust`, `mise install`, or dependency bootstrap after creation.
If setup fails, repair the tracked kit within scope or report a setup defect.

## Lifecycle

Use the installed host `sbx` CLI and an explicit environment path.
If a required host tool is absent, report a setup defect; do not install a replacement.
Keep the reviewed Linux SBX `0.53.0` pin and checksums.
Inside an assigned guest, run repository commands directly; do not create nested SBX.

Keep implementation changes in the assigned feature worktree.
SBX `0.53.0` rejects private clone creation from a Git worktree.
When private creation needs it, use a separate standalone clone of the committed feature branch.
Check its branch and commit against the assignment before creation.
Do not change the main checkout or use uncommitted host files as guest proof.
Preserve the standalone clone because its recovery remote belongs to that clone.

Use task authority for the required environment setup.
Inspect `sbx ls --format json` if its state is unknown.
For a missing environment or changed setup, plan and read the result:

```sh
sbx env plan .sbx/sbxenv.yaml --name <task-sandbox>
sbx env create .sbx/sbxenv.yaml --name <task-sandbox>
```

Native creation builds the local v3 source kit and runs its installation lifecycle.
Record the built kit reference from the output, then inspect the cached artifact through its source path:

```sh
sbx kit inspect ./.sbx/kit --format json
```

Compare the inspected image reference with the creation output.
The short `sbx-kit-src:...` name printed by SBX `0.53.0` is not a valid standalone inspect argument.
Check the packaged files, capabilities, and workload composition against the tracked source.
A plan alone is not build proof.
SBX `0.53.0` cannot validate a v3 source kit with `sbx kit validate --offline`.
Use a native source build and artifact inspection instead, as the [v3 migration guide](https://github.com/docker/sandbox-kit-spec/blob/main/skills/migrate-kit-to-v3/SKILL.md#known-gaps) requires.
For changed setup, use the plan to select the required update or rebuild.
Keep environment removal separate and require explicit authority.
For unchanged setup with valid readiness evidence, reuse the guest with `sbx env exec`.

## Environment readiness

Creation must leave the guest ready before a person or agent starts task work.
Record the effective sandbox name, environment files, mount mapping, and absolute guest workdir.
Use flags before the environment path for `env exec`:

```sh
sbx env exec --name <task-sandbox> .sbx/sbxenv.yaml -- <readiness-command>
```

Use the repository's readiness checks to confirm the harness, runtime tools, trusted configuration, and frozen dependencies.
Run the assigned project check entry point without manual bootstrap first.
Check versions and executable paths, but do not use an installer exit or version alone as proof.
Compare the guest branch, head, base ancestry, remotes, and clean state with the saved assignment.
Check that private Git metadata and new objects belong to the guest clone.
Separate environment state, a missing `PATH` entry, an absent executable, host restrictions, and authentication failures.
Report missing prerequisites instead of silently repairing user configuration.

Find project skills through the repository instructions and the agent's native plugin discovery.
For this plugin, check its deployed `skills/repo-bootstrap/SKILL.md`, `skills/sbx-sandboxes/SKILL.md`, and local reference links.
Use Chezmoi `managed`, `cat`, and `execute-template` to check source classification, rendered content, and plugin capability discovery.
Use an independent temporary destination, config, cache, and state with `CI=1` for preview and apply checks.
For offline discovery checks, use a temporary source copy without `.chezmoiexternals` and `.chezmoiscripts` if Chezmoi expands external sources.
Keep the copied deployment content unchanged.
Scope `diff` and `apply` to the deployed skill targets, exclude scripts and externals, and confirm an empty second diff.
Use `diff --recursive` when the targets are directories.
Do not apply to a live guest or host home for this check.

Also inspect the native shared skill directory and its guest mount options.
Keep that mount read-only; do not apply Chezmoi over it or replace it with a writable copy.
Repository skills and their references must resolve beside the native shared skills without an absent helper or host-only path.
Report absent shared skill content separately from a missing or writable mount.
Check the selected [read-only task context](../../sbx-orchestrator/references/subagent-task.md#read-only-task-context) before launch.
Record readiness evidence and reuse it until setup changes or a failure requires another check.

## Private Git and change return

Use one active writer per private clone and private dependencies.
Native SBX can expose the source read-only at `/run/sandbox/source` and use its existing Git objects as an alternate.
Do not mount host Git metadata or credentials to grant more access.
Private guest changes do not appear in the implementation worktree by themselves.
For an edit/check task, return a patch that includes new files and a report to the assigned location.
The host coordinator reviews and delivers those changes.

For explicit guest delivery, use only the assigned branch, base, remote, and PR scope.
Verify remotes instead of assuming that `origin` is the publishing remote.
Use the native host `sandbox-<name>` recovery remote to retrieve guest commits when needed.
Keep the guest and its standalone source clone until changes and logs are returned and checked.
Do not remove or recreate the guest before recovery is complete.

## Later authority and prerequisites

Credential setup, signing, tracker writes, subagent launch, and release proof are separate from basic setup readiness.
The host coordinator owns credential setup unless the task explicitly assigns it.
Use supported native credential access; do not copy raw tokens or signing keys into the clone or kit.
Approve only the required service mechanisms and domains through native credential bindings before unattended launch.
Confirm usable model access; a CLI login status can report a proxy placeholder even when no binding authorizes requests.
Confirm the selected signing identity and a permitted guest signing method before an assigned signed commit.
For the pilot, transfer only the approved secret signing subkey with native `sbx cp` and import it into the private guest GnuPG directory.
Keep the primary secret key on the host and keep key exports and passphrases out of logs and task data.
Use a scratch signed commit, signature verification, and signing after restart without user input for the later signing proof.
Stop if they are unavailable; do not disable signing or switch identities to continue.
SSH signing defaults are not proof of an assigned signing method.
For assigned tracker work, confirm the existing project tracker, connectivity, and permitted mutations.
Use the project's native latest-state and sync procedure before queue reads and after writes.
For the pilot's Beads replica, require its explicit sync remote and the approved native `bd sync --no-adopt --json` procedure.
Do not initialize, migrate, or redirect it as a bootstrap step.
For assigned subagents, check project delegation rules, available native tools, read-only context, and disjoint write scope first.
Do not launch more workers when the task forbids them.
Stop on authentication or quota failure; do not change account, model, or credentials.

Report exact commands, exits, check counts, warnings, skipped checks, changed files, return locations, active processes, and the session ID when available.
Do not treat direct-mount behavior, SSH signing, or local-model defaults as private-clone pilot proof.
Follow the repository's CI policy; this skill does not require live SBX execution in CI.
Static checks do not prove a native build, guest readiness, credentials, signing, tracker access, or a complete release pilot.
