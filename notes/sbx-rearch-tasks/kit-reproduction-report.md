# SBX kit reproduction report

## Scope

Create a fresh sandbox through the tracked kit.
Do not install tools or change environment variables after creation.
Run actual repository tests with inherited settings.
Preserve existing sandboxes and user work.

Workspace: `/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch`.
Starting revision: `c31934b6`; schema tests became available at `7ace1fcb`.
Final sandbox: `dotfiles-sbx-rearch-kitcheck-pinned`.

## Failure and repair

The first fresh native create, `dotfiles-sbx-rearch-kitcheck`, ran the tracked install script successfully in 34.3 seconds.
It then warned that the guest Docker daemon could not start.
Normal guest exec returned 125 with the same error.
`sbx cp` also required runtime startup and failed, so it could not retrieve guest logs.
Host `sbx diagnose --format json` passed 16 checks, failed none, and skipped two expected checks.
No manual guest daemon repair occurred.

The kit replaced PATH but omitted `/usr/local/sbin`, `/usr/sbin`, and `/sbin`.
Restored these directories in the tracked kit.
A new native create, `dotfiles-sbx-rearch-kitcheck-path`, completed without the runtime warning.
Its tracked install ran automatically in 38.1 seconds.
Guest runtime checks then worked.
This controlled change supports the PATH diagnosis; unavailable guest logs prevent identification of the exact missing daemon command.

## Base pin

The built-in base used mutable tag `docker/sandbox-templates:codex-docker`.
`sbx template ls --format json` reported local image ID `982f4518e7e5`, created `2026-10-28T22:50:17Z`.
Local `sbx template inspect` is unsupported and suggests Docker CLI; that CLI was not used.

Read the primary Docker Hub tag API:

```sh
curl -fsSL https://hub.docker.com/v2/repositories/docker/sandbox-templates/tags/codex-docker/
```

Exit 0.
The returned OCI index digest matches the local image ID:

```text
sha256:982f4518e7e5544e92a23e7fb7eaca9cd5ce9c7178782155a628c92ed723d9de
```

Added that multi-platform digest through supported `sandboxOptions.template`.
The final native plan accepted it.
No external kit repository was created.

## Native commands

All SBX commands ran with the required host platform access.

```sh
sbx kit validate .sbx/kit
sbx env plan --name dotfiles-sbx-rearch-kitcheck-pinned .sbx/sbxenv.yaml
sbx env create --force --name dotfiles-sbx-rearch-kitcheck-pinned .sbx/sbxenv.yaml
```

The first two commands passed.
Final creation result and actual test result are pending below.
Creation log: `/tmp/sbx-rearch-kitcheck-pinned-create.log`.
Earlier PATH repair check log: `/tmp/sbx-rearch-kitcheck-path-checks.log`.

## Required checks

Use only inherited variables in final guest commands, with no `--env` arguments or shell exports.

```sh
sbx env exec --name dotfiles-sbx-rearch-kitcheck-pinned .sbx/sbxenv.yaml -- sh -c 'set -eu; mise --version; mise exec -- uv --version; chezmoi --version; python3 --version; mise exec -- uv python find --no-python-downloads; mise exec -- uv run --frozen pytest tests/integration/test_sbx_workflow.py tests/integration/test_sbx.py -q'
```

The interpreter assertion also checks Python3.14.7, guest-only `sys.prefix`, and these exact inherited values:

```text
UV_PROJECT_ENVIRONMENT=/home/agent/.local/share/dotfiles/venv
UV_PYTHON=/home/agent/.local/share/mise/installs/python/3.14.7/bin/python3
UV_PYTHON_PREFERENCE=system
UV_EXCLUDE_NEWER=P7D
MISE_MINIMUM_RELEASE_AGE=7d
MISE_YES=1
```

## Tracked file hashes

```text
7fb2fc94b7122d1ae818e8a0a141f179eb37cd3024b66812b978e1d46163940d  .sbx/sbxenv.yaml
3b2471691ecaac6a0beedb32b69ea225aedc8d8f4bafbf63ae45e73717334e9d  .sbx/kit/spec.yaml
40d875dcdd2feabb98a1a9d41eb6cac9f201739b6659e192c822f13bcafc209a  .sbx/kit/install.sh
```

## Follow-up limits

Network access to pinned upstream package artifacts and Docker authentication remain external prerequisites.
Native create uses the tracked local kit, npm for exact mise version, mise for pinned runtime tools, and repository lockfile for project dependencies.
It does not depend on a prior guest environment.
Host image layers can be cached; the digest establishes content identity.
The built-in agent setup belongs to the pinned SBX CLI version; a separately published project kit can be considered after this repository migration.

Sources: [Docker environment file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/), [Docker Hub tag metadata](https://hub.docker.com/v2/repositories/docker/sandbox-templates/tags/codex-docker/).

## Final creation and inherited settings

Final native create passed with exit 0.
The log shows the immutable base reference and kit-controlled setup:

```text
setting 10 environment variables
running 2 install commands
sh "$WORKSPACE_DIR/.sbx/kit/install.sh" (kit=dotfiles-toolchain, user=1000)
completed in 43.2s
Created sandbox dotfiles-sbx-rearch-kitcheck-pinned
```

The first ordinary `sbx env exec` started the sandbox and passed all tool and variable assertions.
It reported mise2026.10.23, uv0.12.10, chezmoi2.74.0, and Python3.14.7.
`uv python find --no-python-downloads` returned `/home/agent/.local/bin/python3`.
The isolated project interpreter is `/home/agent/.local/share/dotfiles/venv/bin/python`.
All six inherited variables matched the expected values.
The guest created its own venv; no host `.venv` was used.

Actual final tests are running from the normal repository command, which installs its frozen dependencies as needed.
No `sbx exec` installation command, environment override, post-create script, or manual repair was used in this final sandbox.

The earlier PATH-corrected fresh sandbox passed the same requested tests:

```text
22 passed in 60.02s (0:01:00)
```

Final check log: `/tmp/sbx-rearch-kitcheck-pinned-checks.log`.

## Final acceptance result

Complete.
Final command exit code: 0.

```text
Installed 62 packages in 360ms
......................                                                   [100%]
22 passed in 33.82s
```

Final file hashes match the recorded hashes.
`git diff --check -- .sbx` passed.
Only tracked changes from this proof are the full system PATH in `.sbx/kit/spec.yaml` and the immutable base digest in `.sbx/sbxenv.yaml`.
`.sbx/kit/install.sh` was unchanged.
No commits made.

Kept sandboxes: original `dotfiles-sbx-rearch`; failed `dotfiles-sbx-rearch-kitcheck`; working PATH proof `dotfiles-sbx-rearch-kitcheck-path`; final verified `dotfiles-sbx-rearch-kitcheck-pinned`.
The final verified sandbox is available for the next delegate.
No command or test process remains active from this audit.
No sandbox cleanup, host policy change, credential change, external repository creation, or manual post-create setup occurred.
