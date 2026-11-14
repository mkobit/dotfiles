# Private guest environment

Unit 5 of the [approved pilot design](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot.md#5-reproducible-private-guest-environment) provides the project toolchain and basic guest checks.
The [review record](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot-review.md) defines the proof limits.
Do not run the live pilot from this setup check.

**Status: blocked.**
SBX `0.53.0` cannot run the required offline validation of a v3 source kit.
The required native CI gate remains enabled and will fail with this CLI.
Guest installation and checks remain unproved.

## Workload and tools

The environment uses the native v3 Codex workload `docker.io/docker/sbx-kit-codex:0.155.1`, resolved to:

```text
docker.io/docker/sbx-kit-codex@sha256:f808ef79b5aae10dcfd896dc898e16cbfd806bcd16c9699d208ccb99001eaf76
```

The mixin keeps the workload's native launch command.
Its Dockerfile packages the bootstrap script inside the kit.
Installation does not read a script from a host workspace mount.
The guest uses a private Git clone and private dependencies.
Keep one active writer per clone.
Return later work through the assigned branch and PR.
Native SBX also adds a `sandbox-NAME` Git remote on the host for change recovery.
Preserve guest changes and logs before removal or recreation.

Keep the Linux SBX `0.53.0` catalog pin and checksums.
Use the official macOS cask on supported Apple silicon hosts.
See [kit compatibility](https://docs.docker.com/ai/sandboxes/customize/use-kits/) and [v3 mixins](https://docs.docker.com/ai/sandboxes/customize/author/tool-mixins/).

## Check and create

Run from a clean, committed feature worktree based on the accepted `origin/main`.
The private clone starts from the committed head.
Commit the intended setup before guest proof; uncommitted host files are not guest evidence.
Use an explicit environment path to avoid implicit host environment defaults.
Use the same unique name with every environment command.

```sh
sbx kit validate .sbx/kit --offline
sbx env plan .sbx/sbxenv.yaml --name dotfiles-unit5-proof
sbx env create .sbx/sbxenv.yaml --name dotfiles-unit5-proof
```

`env create` prepares the guest without starting a Codex task.
Read the plan before creation.
Stop if it requires credential setup or an unrelated host change.
Do not use `env run` for basic checks.
Run commands with native `env exec`:

```sh
sbx env exec .sbx/sbxenv.yaml --name dotfiles-unit5-proof -- sh -c '
  set -eu
  cd "${WORKSPACE_DIR:?}"
  test -d .git
  git rev-parse --show-toplevel
  git rev-parse --absolute-git-dir
  git rev-parse HEAD
  git branch --show-current
  git remote -v
  git status --porcelain
  mise --version
  uv --version
  python3 --version
  chezmoi --version
  bd --version
  gh --version
  gpg --version
  git --version
  tar --version
  unzip -v
  codex --version
  mise exec -- uv sync --all-packages --frozen
  git diff --exit-code -- uv.lock
  mise run verify
'
```

Compare the guest head, branch, repository identity, and clean state with the saved host values.
Check that the absolute Git directory is inside the private guest clone.
A version command or installer exit alone does not prove repository verification.
Record the full check result and the commit tested.

Use a temporary destination and separate Chezmoi config, cache, and state for apply proof.
Set `CI=1` to suppress secret prompts.
Preview with `chezmoi diff`, then run `chezmoi apply` with the same explicit paths.
Do not use the guest or host home directory as the test destination.
Record any excluded targets or scripts; a limited apply does not prove a full apply.

## CI and local checks

```sh
mise run test:workflow
mise run verify
mise exec -- uv run --frozen pytest tests/integration/test_sbx_project_environment.py -m 'not integration'
```

Portable checks test the packaged references and private environment configuration.
They do not prove native SBX behavior.
Enabled Linux and macOS CI jobs must run native `sbx kit validate --offline` on the local kit source.
A missing CLI fails those jobs.
Hosted CI does not prove guest startup or environment planning.

## Required later inputs

Before the live pilot, supply the repository, allowed queue scope, assigned branch and base policy, tracker identity and native sync remote, available models, signing-subkey identity, and return location.
Keep tracker state separate from the private Git clone.
For Beads `1.3.2`, configure the approved replica and remote during the later setup unit.
Use its native project sync process before queue reads and after writes; the approved design uses `bd sync --no-adopt --json` with an explicit remote.
This unit does not initialize or change a tracker.

Configure repository-scoped GitHub access through native SBX service-secret bindings in the later credential unit.
The token itself must restrict repository access; a sandbox binding does not do that.
Do not mount a host credential resolver in a guest-writable path.

The later signing unit must transfer only the approved secret signing subkey with native `sbx cp` and import it into the private guest GnuPG directory.
Keep the primary secret key outside the guest.
Keep exports and passphrases out of Git, images, command arguments, logs, and task records.
Signing, restart, tracker sync, model, and subagent proof remain later prerequisites.

## Validation record

Checks on 2026-11-13 used base `f1b0c389745e3fdac64d2421d5c122d765b5081d` plus this unit's changes.
The Linux catalog pin and frozen lockfile have no changes.

| Check | Result |
| --- | --- |
| Native workload inspection | Resolved the Codex `0.155.1` tag to the digest above; schema `3`, native `codex` entrypoint. |
| Native environment plan | Passed with SBX `0.53.0` (`2c628380`); private clone, pinned workload, local mixin, and host recovery remote listed. Planning does not build or validate the source kit. |
| Packaged native offline validation | Failed with SBX `0.53.0`: `v3 source kit and this load path has no kit builder configured`. The enabled integration test reproduces this failure. |
| Native `kit pack` | Rejected the v3 source fields `dockerfile` and `capabilities`. It does not provide a source ZIP workaround. |
| `mise run verify` | Passed: 447 Python tests, 49 portable workflow tests, Ruff, ty, and package builds. One native integration test is excluded from the portable task and runs separately. |
| Shell checks | `sh -n` and ShellCheck `0.11.0` passed. |
| macOS native validation | Pending CI. The required source check has the same known SBX limitation. |
| Fresh guest | Pending. Git metadata, tools, frozen dependencies, repository verification, and isolated apply have no guest proof. |

Host checks used mise `2026.11.0`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.72.0`, pytest `9.1.1`, Ruff `0.17.3`, and ty `0.0.92`.
These are host test versions.
The installer selects mise `2026.10.23`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.74.0`, and Beads `1.3.2`; their guest installation remains unproved.
System packages use the workload's APT sources; record their resolved versions when guest proof can run.
The macOS `0.53.0` installation and CLI proof belongs to [unit 3, PR #1066](https://github.com/mkobit/dotfiles/pull/1066).

The [official v3 migration guide](https://github.com/docker/sandbox-kit-spec/blob/main/skills/migrate-kit-to-v3/SKILL.md#known-gaps) confirms that `sbx kit validate` cannot accept a v3 source kit.
It requires a build, then inspection of the built artifact.
A built artifact check would change the approved offline source-validation requirement.
Keep this unit blocked until a supported native source check passes or that requirement is revised.
Do not replace the gate with YAML parsing or a generated legacy descriptor.

The host daemon reported `0.51.0` and healthy virtualization.
Later host commands reported CLI `0.53.0`; daemon-backed kit validation requested a restart to match versions.
No host binary or daemon change was made by this unit.
A restart would stop other running sandboxes, so guest creation was not attempted.
No signing key, tracker, credential setup, or live pilot operation was used.
