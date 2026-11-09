# Guest workflow task contract

## Decision

Install one native global Mise file task through the existing tracked repository kit.
Use `.sbx/kit/files/home/.config/mise/tasks/pr/ship` as its tracked source.
SBX maps it to `/home/agent/.config/mise/tasks/pr/ship`.
Add `chmod 0755 /home/agent/.config/mise/tasks/pr/ship` to the existing kit install script, after its Python installation.
Do not write a guest `config.toml` or copy the host Mise configuration.
No separate kit repository or manual guest installation is needed.

Mise loads files in `$MISE_CONFIG_DIR/tasks` as global tasks, even when no global configuration file exists.
Nested task paths use colon-separated task names.
See [global task discovery](https://mise.jdx.dev/tasks/task-discovery.html#global-tasks) and [file tasks](https://mise.jdx.dev/tasks/file-tasks.html).
The existing kit uses the standard `/home/agent` configuration directory.
If a future kit changes `MISE_CONFIG_DIR`, it must install the task in that configured directory.

Use this file metadata:

```sh
#!/bin/sh
#MISE description="Ship the assigned pull request"
#MISE dir="{{cwd}}"
#MISE raw_args=true
```

Mise supports `dir = "{{cwd}}"` and exports the caller directory as `MISE_ORIGINAL_CWD`.
`raw_args` passes all task arguments, including `--help`, to the wrapped parser.
See [task directory and raw arguments](https://mise.jdx.dev/tasks/task-configuration.html).
Without `raw_args`, the current CLI intercepts `--help` and says the task accepts no arguments.

Keep the four public workflow commands from `tasks.md`.
Only guest `pr:ship` needs a guest file task for this route.
The three host coordinator commands remain host tasks.
An internal helper option does not create another public task.

## Wrapper contract

Resolve the Git root from the caller directory with an argument-safe command:

```sh
repo=$(git -C "${MISE_ORIGINAL_CWD:?Mise invocation directory is required}" rev-parse --show-toplevel)
context="$repo/.sbx/task-context"
```

Never derive the caller repository from the task file location or the guest home directory.
Use `set -eu` and give an actionable error when Git root resolution fails.
Require the runtime helper, runtime JSON, assignment snapshot, and the kit's pinned Python path.
Missing assets must stop before any publication and say to run the host launch command that prepares the context.

Recommended internal helper invocation:

```sh
exec /home/agent/.local/share/mise/installs/python/3.14.7/bin/python3 \
  "$context/dotfiles-agent.py" \
  --repo "$repo" \
  --config "$context/runtime.json" \
  pr:ship "$@"
```

`--repo` and `--config` are proposed internal parser options, not verified existing helper flags.
The implementation must use the same flags in its host tasks, parser, and guest wrapper.
Only fixed executable syntax belongs in the wrapper.
Use `"$@"` for all user arguments.
Python must use argument lists and `shell=False` for subsequent commands.

## Runtime assets and ownership

The host coordinator owns creation and validation of these run inputs:

| File | Content |
| --- | --- |
| `.sbx/task-context/dotfiles-agent.py` | A byte copy of the deployed standalone host helper |
| `.sbx/task-context/runtime.json` | An allowlisted guest runtime projection |
| `.sbx/task-context/assignment.json` | The full frozen assignment snapshot and run identity |
| `.sbx/task-context/state/` | Guest workflow evidence and pending merge result |

The helper's canonical source remains `src/chezmoi/dot_local/bin/tools/executable_dotfiles-agent.py`.
Chezmoi deploys that file to `.local/bin/tools/dotfiles-agent.py` below its destination directory.
The host exports its deployed helper, not an unrelated file from the consuming repository.
Do not create a uv package or runtime dependencies.

The runtime projection must identify schema version, run ID, bead ID, expected repository/remote/base/head branch, actor, `host-coordinator` tracker route, host-close requirement, snapshot path/hash, required check policy, and a guest-local state directory.
Reuse the implementation's existing schema rather than adding parallel configuration fields.
Copy only needed workflow defaults.
Do not copy host absolute state paths, tracker connection settings, credentials, environment dumps, or whole home configurations.
Set the guest state directory to `.sbx/task-context/state` using its resolved guest absolute path.
The host keeps its authoritative record, expected identities, and material snapshot hash outside guest-controlled state.
Guest assets are run inputs, not a source of authority for host close.

Ignore `.sbx/task-context/` in the consuming repository so run inputs do not make shipping dirty.
Reject symlinks and an unexpected existing context or run ID before export.
Use atomic file replacement and private directory permissions.
One recorded writer owns the checkout and context.
Do not silently replace another launch's context.

The tracked kit owns installation of the static wrapper and pinned runtime.
The host launch coordinator owns asset preparation and transfer, plus claim and close.
The guest helper owns verification and authorized PR delivery through merge confirmation.
It must return the pending host-close result and must not invoke Beads.
A standalone invocation without a valid explicit host-coordinator contract must fail.

## Direct and clone transport

Direct mode uses the workspace mount for `.sbx/task-context/`.
Create and verify the runtime assets before worker launch.
Do not assume that guest home files are shared with the host.

Clone mode needs explicit native copy after the clone exists and before worker launch.
Create the exact destination directory with an argument-list invocation:

```text
sbx exec --workdir GUEST_REPO NAME mkdir -p GUEST_REPO/.sbx/task-context
sbx cp HOST_CONTEXT/dotfiles-agent.py NAME:GUEST_REPO/.sbx/task-context/dotfiles-agent.py
sbx cp HOST_CONTEXT/runtime.json NAME:GUEST_REPO/.sbx/task-context/runtime.json
sbx cp HOST_CONTEXT/assignment.json NAME:GUEST_REPO/.sbx/task-context/assignment.json
```

Call these with `subprocess.run([...], shell=False)`; the displayed uppercase tokens are individual argument values.
Use the validated guest repository path saved in the launch record.
Copy individual files to avoid directory nesting on retries.
SBX copies the source directory itself and changes behavior when the destination directory already exists.
It also rejects workspace symlinks that escape the workspace.
See [native SBX copy](https://docs.docker.com/reference/cli/sbx/cp/).

Run `sbx exec --workdir GUEST_REPO NAME mise tasks ls --json` to prove the discovered `pr:ship` source is the kit-installed task.
A repository-local task with the same name can shadow it; reject an unexpected source.
Validate the copied files and run identity before the claim where possible and again before the worker starts.
The complete claimed assignment snapshot can only be exported after the host claim.
A copy failure after claim retains the claim and launch record.

The clone return remote contract and edit-only linked-worktree exception remain those in `tracker-route.md`.
This mechanism does not make an unreachable host worktree Git metadata path available in the guest.

## Python baseline

Use the existing kit Python 3.14.7 through its absolute path.
This meets the repository's existing Python 3.14 baseline and adds no installation.
It prevents the caller repository's Python tool selection from choosing the helper interpreter.
Do not add `uv run`, task-specific Python tools, or a second Python install.
Verification still invokes the repository's own `mise run verify` and thus uses that repository's normal configuration.

Mise can still check or install missing repository tools before it starts any task.
The wrapper cannot prevent that while preserving repository settings.
The existing kit must satisfy its repository tool prerequisites; fail preflight for missing tools.
Do not disable locked mode or release-age controls to bypass this prerequisite.

For host execution, retain `python3` and the existing supported baseline.
Check its version before claim and give an actionable failure if it is below the helper baseline.
Do not lower the helper's baseline without a compatibility test.
A broader cross-repository runtime baseline is follow-up work.

## Evidence

Installed CLI: Mise `2026.10.23 linux-x64 (2026-10-29)`.
All fixture files are under `/tmp/sbx-rearch-guest-task-fixture/`.
No install command, live user configuration change, sandbox creation, credential change, or repository edit was performed.

`results.json` records successful global discovery without `config.toml` and execution from `repo/nested`.
The discovered task reports `global: true` and `dir` equal to the nested caller directory.
The executed task reports matching `cwd` and `MISE_ORIGINAL_CWD`.
Arguments containing spaces, shell substitution text, and flags remain single unchanged argument values.
`raw-args-results.json` proves that `--help` reaches the wrapped process after `raw_args=true` is added.
`preservation-results.json` proves that an existing global configuration remains byte-identical and that an absolute Python path bypasses a caller PATH override.
`python-pin-results.json` proves that Mise selects the fixture repository Python 3.12.0 as active and installed, while the wrapper still executes the explicit Python 3.14.7 interpreter.
The fake repository interpreter exits 86 if called; both recorded commands instead exit zero.
All completed recorded fixture commands exit zero.

The fixture execution uses an existing Python executable outside the fixture as read-only runtime input.
The runtime output body is a JSON probe, not the pending real workflow helper.
These are discovery and argument-transport tests, not a full shipping test.

## Required implementation tests

- Install and discover the task in a fresh repository-owned kit environment.
- Keep the guest global tools/settings file byte-identical.
- Run from nested paths and repository paths containing spaces.
- Pass `--help`, a bead ID, and literal shell syntax without evaluation.
- Confirm that a conflicting repository Python pin does not choose the helper interpreter.
- Reject missing/mismatched runtime files before Git push or PR creation.
- Reject an unexpected `pr:ship` task source.
- Test direct asset visibility and native clone copies, including retry destinations.
- Verify that no guest command invokes Beads and no runtime projection exposes host state paths.
- Confirm that host close uses only the saved host tracker identity and snapshot.
- Preserve pending state after copy, worker, merge-confirmation, or host-close failure.

A fresh SBX lifecycle test and real native file transfer remain integration prerequisites.
The investigation checked installed command help and official references; it did not run those lifecycle operations.

## Primary sources

- [Mise global task discovery](https://mise.jdx.dev/tasks/task-discovery.html#global-tasks).
- [Mise file tasks and executable scripts](https://mise.jdx.dev/tasks/file-tasks.html).
- [Mise task configuration: caller directory and raw arguments](https://mise.jdx.dev/tasks/task-configuration.html).
- [Mise task environment](https://mise.jdx.dev/tasks/running-tasks.html#task-environment).
- [SBX kit static files and setup order](https://docs.docker.com/ai/sandboxes/customize/kits-v2/#static-files).
- [SBX native file copy](https://docs.docker.com/reference/cli/sbx/cp/).

The online Mise documentation currently describes v2026.11.0.
The isolated CLI tests establish the specific behavior used here for the installed 2026.10.23 version.
