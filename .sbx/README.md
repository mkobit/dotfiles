# Private guest environment

Unit 5 of the [approved pilot design](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot.md#5-reproducible-private-guest-environment) provides the project toolchain and basic guest checks.
The [review record](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot-review.md) defines the proof limits.
Do not run the live pilot from this setup check.

**Status: guest proof pending.**
Hosted CI checks the package and the installed SBX CLI.
Native source build and guest checks require a capable host.
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

Keep implementation changes in the assigned feature worktree.
SBX `0.53.0` rejects private clone creation from a Git worktree.
Use a separate temporary standalone clone of the committed feature branch for guest proof.
Check its commit and branch before creation; do not change the main checkout or merge the design branch.
Run the commands below from that standalone clone.
The private clone starts from the committed head.
Commit the intended setup before guest proof; uncommitted host files are not guest evidence.
Use an explicit environment path to avoid implicit host environment defaults.
Use the same unique name with every environment command.
For `env exec`, put flags before the environment path.

```sh
sbx env plan .sbx/sbxenv.yaml --name dotfiles-unit5-proof
sbx env create .sbx/sbxenv.yaml --name dotfiles-unit5-proof
```

`env create` prepares the guest without starting a Codex task.
Read the plan before creation.
Native creation builds the local v3 source kit.
A successful plan alone does not validate that build.
Stop if it requires credential setup or an unrelated host change.
Do not use `env run` for basic checks.
Run commands with native `env exec`:

```sh
sbx env exec --name dotfiles-unit5-proof .sbx/sbxenv.yaml -- sh -c '
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
mise exec -- uv run --frozen pytest tests/integration/test_sbx_project_environment.py
```

Linux and macOS CI run the package tests after installing frozen dependencies.
The tests check packaged bootstrap references, shell syntax, private clone configuration, and bootstrap input failures.
CI also requires the installed SBX CLI to report its version.
A missing CLI fails that check.

This corrects the design's unsupported offline source-validation command.
SBX `0.53.0` cannot validate a v3 source kit with `sbx kit validate --offline`.
The [official migration guide](https://github.com/docker/sandbox-kit-spec/blob/main/skills/migrate-kit-to-v3/SKILL.md#known-gaps) requires a native source build, then inspection of the built artifact.
Keep that proof on a capable host, followed by the guest checks above.
Hosted package checks do not prove a native build, guest startup, or readiness for the pilot.
Do not mark unit 5 complete from green hosted CI alone.

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

Initial checks on commit `0af07aa7` used base `f1b0c389745e3fdac64d2421d5c122d765b5081d` plus this unit's changes.
The Linux catalog pin and frozen lockfile have no changes.

| Check | Result |
| --- | --- |
| Native workload inspection | Resolved the Codex `0.155.1` tag to the digest above; schema `3`, native `codex` entrypoint. |
| Native environment plan | Passed with SBX `0.53.0` (`2c628380`); private clone, pinned workload, local mixin, and host recovery remote listed. Planning does not build or validate the source kit. |
| Packaged native offline validation | Failed with SBX `0.53.0`: `v3 source kit and this load path has no kit builder configured`. The initial integration test reproduced this failure. |
| Native `kit pack` | Rejected the v3 source fields `dockerfile` and `capabilities`. It does not provide a source ZIP workaround. |
| `mise run verify` | Passed: 447 Python tests, 49 portable workflow tests, Ruff, ty, and package builds. This was the initial portable check result. |
| Shell checks | `sh -n` and ShellCheck `0.11.0` passed. |
| Initial hosted native validation | [CI run 43544369158](https://github.com/mkobit/dotfiles/actions/runs/43544369158) failed at the same unsupported source check on Linux amd64, Linux arm64, and macOS. |
| Fresh guest | Pending. Git metadata, tools, frozen dependencies, repository verification, and isolated apply have no guest proof. |

Host checks used mise `2026.11.0`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.72.0`, pytest `9.1.1`, Ruff `0.17.3`, and ty `0.0.92`.
These are host test versions.
The installer selects mise `2026.10.18`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.74.0`, and Beads `1.3.2`; their guest installation remains unproved.
System packages use the workload's APT sources; record their resolved versions when guest proof can run.
The macOS `0.53.0` installation and CLI proof belongs to [unit 3, PR #1066](https://github.com/mkobit/dotfiles/pull/1066).

The [official v3 migration guide](https://github.com/docker/sandbox-kit-spec/blob/main/skills/migrate-kit-to-v3/SKILL.md#known-gaps) confirms that `sbx kit validate` cannot accept a v3 source kit.
It requires a build, then inspection of the built artifact.
The CI correction separates supported hosted package checks from required native build and guest proof.
No generated legacy descriptor or successful hosted test counts as native validation.

The host daemon reported `0.51.0` and healthy virtualization.
Later host commands reported CLI `0.53.0`; daemon-backed kit validation requested a restart to match versions.
No host binary or daemon change was made by this unit.
A restart would stop other running sandboxes, so guest creation was not attempted.
No signing key, tracker, credential setup, or live pilot operation was used.

## Native proof follow-up

On commit `b126067fe6dccf72d2118be33a4fb90d900c5a82`, the host CLI and daemon both reported `0.53.0`.
`sbx diagnose --format json` reported 16 passes, no warnings, no failures, and four skips.
KVM was accessible.
No daemon restart or unrelated sandbox stop was needed.

`sbx env create .sbx/sbxenv.yaml --name dotfiles-unit5-proof --force` built the local v3 mixin in eight seconds as `sbx-kit-src:spec-b57bff4737c9`.
It then rejected the Git worktree as a private clone source.
A temporary standalone clone of the same branch and commit passed that check.
The pinned workload was pulled and assembled with the mixin into 21 layers.
The system package install passed.
The native workload used its stored OAuth setup automatically; no coding task started and no manual credential setup was performed.

`sbx kit inspect ./.sbx/kit --format json` read the cached built artifact through the native source resolver.
It reported schema `3`, kind `mixin`, the built image above, network rules, and both install hooks.
Direct inspection through the local registry was denied by the host source allowlist.
No policy was changed.

Project installation failed because `mise@2026.10.23` was too new for the required 21-day npm cutoff.
The [npm registry metadata](https://registry.npmjs.org/mise) reports publication on `2026-10-29T10:15:06.412Z`.
The corrected pin, `2026.10.18`, was published on `2026-10-23T11:58:40.295Z` and meets the failed run's `2026-10-24T05:50:09Z` cutoff.
The release-age limits remain enabled.
A behavioral regression test checks both supported shells against this cutoff.

The failed creation left no registered proof guest.
Native build and artifact inspection have passed for the initial source.
Guest Git metadata, tools, frozen dependencies, repository verification, and isolated apply remain pending until a fresh creation with the corrected source passes.
