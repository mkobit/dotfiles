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
