# dotfiles

[![CI](https://github.com/mkobit/dotfiles/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mkobit/dotfiles/actions/workflows/ci.yml)

Personal dotfiles managed with `chezmoi` and `mise`.
See [workflow dependencies](.github/workflows/README.md) for Actions locks and update policy.

Chezmoi installs pinned GitHub CLI extensions with local registration; see [extension configuration and updates](src/chezmoi/dot_local/share/gh-managed/README.md).

## Setup output

Messages from the shared shell log helper include UTC timestamps.
Use the time between messages to locate slow install steps.
The plugin bridge prints a start and end record for each host CLI call to standard error.
Each end record includes elapsed seconds and the exit status.
These records name the host and operation, without command arguments or captured output.
A start record without an end record shows that the call did not report completion.
The bridge keeps its existing command execution and output capture.
Logging failures do not stop setup.

## Pull requests and releases

Open a pull request for changes to `main`.
Wait for the required CI checks to pass, then squash merge.
If this repository starts publishing releases, use an unprefixed UTC CalVer tag such as `2026.11.5`.
