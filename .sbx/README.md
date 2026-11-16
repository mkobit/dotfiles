# Private guest environment

Unit 5 of the [approved pilot design](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot.md#5-reproducible-private-guest-environment) provides the project toolchain and basic guest checks.
The [review record](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot-review.md) defines the proof limits.
Do not run the live pilot from this setup check.

**Status: native build and basic fresh-guest proof passed.**
The tested source commit is `4fe3d1ae466e629bbdfebd2f23cd649ec7721b30`.
Chezmoi apply proof excludes scripts and externals.
Full apply and the later pilot prerequisites remain unproved.
Hosted CI checks the package and the installed SBX CLI; it does not supply guest proof.

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
The installer selects mise `2026.10.18`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.74.0`, and Beads `1.3.2`; their guest versions are confirmed in the follow-up below.
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

## Corrected-source guest proof

The corrected source commit `4fe3d1ae466e629bbdfebd2f23cd649ec7721b30` passed native build, artifact inspection, fresh creation, and command-only guest checks on Linux amd64 with CLI and daemon `0.53.0`.
The private guest is `dotfiles-unit5-proof-fixed`.
The source is the temporary standalone clone at `/tmp/sbx-unit5/proof-source`.
The implementation worktree remains `/home/mkobit/.codex/worktrees/430c/chezmoi` on `feat/sbx-private-guest`.
The approved design branch remains at `c4d122a7`.

The corrected mixin built in two seconds as `sbx-kit-src:spec-d46798f371f0`.
Native source inspection reported schema `3`, kind `mixin`, that image, and both install hooks.
The workload digest is unchanged from the value above.
System installation passed in `42.3s`; project installation and frozen dependency setup passed in `115.2s`.
Native creation reported that no binding authorized OpenAI credential injection.
No credential binding was added and no coding task started.

Commands used from the temporary clone:

```sh
git fetch origin feat/sbx-private-guest
git merge --ff-only origin/feat/sbx-private-guest
sbx env create .sbx/sbxenv.yaml --name dotfiles-unit5-proof-fixed --force
sbx kit inspect ./.sbx/kit --format json
sbx env exec -i --name dotfiles-unit5-proof-fixed .sbx/sbxenv.yaml -- sh < /tmp/sbx-unit5/guest-proof.sh
sbx env exec -i --name dotfiles-unit5-proof-fixed .sbx/sbxenv.yaml -- sh < /tmp/sbx-unit5/guest-apply.sh
```

The proof scripts and complete logs remain in `/tmp/sbx-unit5/`.
These local records are temporary and are not repository dependencies.
The Git proof asserted the tested head, branch `feat/sbx-private-guest`, base ancestry from `f1b0c389745e3fdac64d2421d5c122d765b5081d`, and an empty `git status --porcelain` before and after verification.
Both the absolute Git directory and common Git directory were `/tmp/sbx-unit5/proof-source/.git` inside the guest.
There was no `commondir` file.
Native SBX uses `/run/sandbox/source` as origin and `/run/sandbox/source/.git/objects` as a read-only object alternate.
Git metadata and new objects belong to the private guest; existing objects use that native source mount.
The host recovery remote is in the temporary source clone.
Preserve that clone with the guest.

| Guest tool | Version |
| --- | --- |
| mise | `2026.10.18` |
| uv | `0.12.10` |
| Python | `3.14.7` |
| Chezmoi | `2.74.0` |
| Beads | `1.3.2` (`9b65b9e19`) |
| Codex | `0.155.1` |
| Git | `2.53.0` |
| GitHub CLI | `2.46.0` |
| GnuPG | `2.4.8` |
| tar | `1.35` |
| zip / unzip | `3.0` / `6.0` |
| xz / gzip | `5.8.3` / `1.14` |
| Node.js / npm packages | `22.22.1+dfsg+~cs22.19.15-1ubuntu1` / `9.2.0~ds3-1` |

`dpkg-query -W` recorded package revisions for all APT prerequisites in `guest-proof.log`.
`mise exec -- uv sync --all-packages --frozen` and `git diff --exit-code -- uv.lock` passed.
`mise run verify` passed: 447 unit tests, 57 workflow tests, Ruff, formatting, ty, and all package builds.
The clone remained clean.
Mise warned that global Chezmoi, Python, and Beads pins are absent from the repository mise lockfile.
Those warnings did not fail the checks; no lockfile or release-age setting was changed.

The isolated Chezmoi script used `CI=1`, `mktemp -d /tmp/dotfiles-unit5-apply.XXXXXX`, and separate `--destination`, `--config`, `--cache`, and `--persistent-state` paths.
It ran `chezmoi init --no-tty`, then `diff`, `apply`, and a second `diff`, with `--exclude=scripts,externals` on all diff/apply commands.
All commands passed and the second diff was empty.
The destination was `/tmp/dotfiles-unit5-apply.8R0Mhv/dest` inside the guest.
Chezmoi warned that managed Codex settings can canonicalize formatting.
No guest home configuration was used as the apply destination.
This is limited apply proof; installation scripts, external downloads, and full apply remain unproved.

Host verification also passed 447 unit tests and 57 workflow tests.
The regression test failed against the previous pin in both shells, then passed with the corrected pin.
Independent review found no blocking issue before the corrected-source commit.
All eight [PR checks on the tested source](https://github.com/mkobit/dotfiles/actions/runs/43624967254) passed, including Linux amd64, Linux arm64, and macOS integration.
The draft PR remains open.
Signing, tracker sync, credential setup, models, subagents, restart proof, and live delivery remain later work.

## Prepare a dedicated GPG signing subkey from KeePass

Run these steps in a trusted host terminal, outside every sandbox and repository mount.
Keep the original KeePass backup unchanged.
Use an isolated keyring throughout; these commands do not import private keys into your normal keyring.
See the [GnuPG key-management manual](https://www.gnupg.org/documentation/manuals/gnupg/OpenPGP-Key-Management.html) and [command reference](https://www.gnupg.org/documentation/manuals/gnupg26/gpg.1.html).

### 1. Inspect the backup

Create a private setup directory and print the attachment export path:

```sh
umask 077
signing_setup=$(mktemp -d "${XDG_RUNTIME_DIR:-/tmp}/sbx-signing.XXXXXX")
source_ring="$signing_setup/source-ring"
check_ring="$signing_setup/check-ring"
mkdir -m 700 "$source_ring" "$check_ring"
printf 'Export the KeePass GPG attachment to: %s\n' "$signing_setup/backup.asc"
```

Save the GPG attachment from KeePass to that path.
If the key is stored as protected text, save only that key block with your KeePass client or a trusted local editor outside the agent workspace.
Do not export the KeePass database itself or paste key contents into a terminal or chat.
Inspect the attachment without importing it:

```sh
gpg --homedir "$source_ring" --import-options show-only --dry-run \
  --import "$signing_setup/backup.asc"
```

Check the identity and fingerprint against the key you intend to use.
Then import into the isolated host keyring and list its secret-key availability:

```sh
gpg --homedir "$source_ring" --import "$signing_setup/backup.asc"
gpg --homedir "$source_ring" --list-secret-keys --with-subkey-fingerprint
```

An ordinary `sec` entry means the primary secret key is available.
`sec#` means it is unavailable; a subkey-only backup cannot create another subkey.
`sec>` refers to a smartcard and requires that card.
Stop here if the primary secret key is unavailable; retrieve the primary backup rather than substituting your normal signing subkey.

### 2. Create the sandbox subkey

Set the full primary fingerprint from the inspected output, then create a signing-only subkey with a one-year expiry:

```sh
primary_fpr='REPLACE_WITH_FULL_PRIMARY_FINGERPRINT'
gpg --homedir "$source_ring" --quick-add-key "$primary_fpr" ed25519 sign 1y
gpg --homedir "$source_ring" --list-secret-keys --with-subkey-fingerprint "$primary_fpr"
```

Enter the existing key passphrase through GnuPG's prompt.
Do not put it in command arguments, environment variables, or logs.
Copy the full fingerprint of the new Ed25519 `[S]` subkey:

```sh
sandbox_subkey_fpr='REPLACE_WITH_NEW_SUBKEY_FINGERPRINT'
gpg --homedir "$source_ring" --armor \
  --output "$signing_setup/selected-subkey.asc" \
  --export-secret-subkeys "${sandbox_subkey_fpr}!"
gpg --homedir "$check_ring" --import "$signing_setup/selected-subkey.asc"
gpg --homedir "$check_ring" --list-secret-keys --with-subkey-fingerprint "$primary_fpr"
```

Require `sec#` for the primary key and exactly one usable secret subkey: the selected `[S]` subkey.
Other public subkeys or `ssb#` entries are allowed; other usable secret subkeys are not.
The trailing `!` selects the exact subkey and must remain in the export command.

### 3. Prepare unattended signing

Unattended signing after restart needs a copy the guest can use without a passphrase prompt.
This route removes the passphrase only in the isolated, subkey-only keyring.
The original backup and source keyring remain unchanged.
The exported subkey permits signing until expiry or revocation; it is not restricted to one repository.
GitHub credential scopes separately limit publication access.

```sh
gpg --homedir "$check_ring" --change-passphrase "$primary_fpr"
```

Enter the old passphrase when requested, then leave the new passphrase empty and confirm that choice.
Stop if you do not want a passphrase-free sandbox subkey; do not claim restart-safe signing from a cached passphrase.
Export only this isolated signing subkey, plus the updated public certificate:

```sh
gpg --homedir "$check_ring" --armor \
  --output "$signing_setup/sandbox-signing.asc" \
  --export-secret-subkeys "${sandbox_subkey_fpr}!"
gpg --homedir "$source_ring" --armor \
  --output "$signing_setup/public.asc" --export "$primary_fpr"
chmod 600 "$signing_setup/sandbox-signing.asc"
```

### 4. Check signing without a cached passphrase

Test the file that will be handed to the agent in a fresh isolated keyring:

```sh
proof_ring="$signing_setup/proof-ring"
mkdir -m 700 "$proof_ring"
gpg --homedir "$proof_ring" --import "$signing_setup/sandbox-signing.asc"
gpg --homedir "$proof_ring" --list-secret-keys --with-subkey-fingerprint "$primary_fpr"
```

Again require `sec#` and exactly the selected usable signing subkey.
Then check signing after its agent restarts:

```sh
printf 'Sandbox signing bootstrap check\n' > "$signing_setup/proof.txt"
gpgconf --homedir "$proof_ring" --kill gpg-agent
gpg --homedir "$proof_ring" --batch --pinentry-mode error \
  --local-user "${sandbox_subkey_fpr}!" \
  --output "$signing_setup/proof.sig" --detach-sign "$signing_setup/proof.txt"
gpg --homedir "$proof_ring" --batch --status-fd 1 \
  --verify "$signing_setup/proof.sig" "$signing_setup/proof.txt"
```

Require a successful exit and a `VALIDSIG` record naming the selected subkey fingerprint.
If signing asks for input or fails, stop before guest import.

### 5. Save and hand back the selected subkey

Save the new subkey export, public certificate, fingerprint, and expiry in a separate KeePass entry.
Do not replace the primary-key backup with the subkey-only export.
Give the agent only the new public fingerprint and the local path to `sandbox-signing.asc`.
Keep `backup.asc`, the source keyring, and all passphrases out of the guest, clone, kit, task data, and logs.
The agent can transfer only the selected subkey with native `sbx cp`, configure the exact Git signing identity, and verify a scratch signed commit before and after guest restart.
Only `public.asc` is suitable for GitHub public-key registration; do not remove an existing account key to resolve an unexamined duplicate-key error.

Keep the setup directory private until backup and guest verification finish.
Then close its GPG agents and remove the setup directory with assistance if needed.
Never remove your normal GnuPG directory or the original KeePass backup.

The exact-subkey export and restarted-agent signing procedure was checked with disposable keys in the private SBX guest on 2026-11-16.
No real user key was used in that check.
KeePass export, interactive passphrase changes, real-key provisioning, GitHub registration, and full guest restart remain manual or live proof steps.
