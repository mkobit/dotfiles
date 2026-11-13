# dotfiles

[![CI](https://github.com/mkobit/dotfiles/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mkobit/dotfiles/actions/workflows/ci.yml)

Personal dotfiles managed with `chezmoi` and `mise`.

## Setup output

Messages from the shared shell log helper include UTC timestamps.
Use the time between messages to locate slow install steps.
The plugin bridge prints a start and end record for each host CLI call to standard error.
Each end record includes elapsed seconds and the exit status.
These records name the host and operation, without command arguments or captured output.
A start record without an end record shows that the call did not report completion.
The bridge keeps its existing command execution and output capture.
Logging failures do not stop setup.

## Pi

[Pi v1.5.2](https://github.com/earendil-works/pi/releases/tag/v1.5.2) uses the full release archive in `.local/share/pi` and a `.local/bin/pi` link.
Set `data.local.bin.pi.installation_method` to `github_releases` to install it, or `existing` to configure an existing installation.
An absent method leaves Pi files unchanged.
Set `none` to remove only `.pi/agent/settings.json`; the binary, archive, authentication, sessions, and other resources remain.

Set native [Pi settings](https://github.com/earendil-works/pi/blob/v1.5.2/packages/coding-agent/docs/settings.md) under `data.pi.settings`.
Each configured top-level key replaces the current value; other keys remain.
Maps and lists replace the whole value, and an empty list clears it.
The base configuration sets `cacheWarming = "off"`.
