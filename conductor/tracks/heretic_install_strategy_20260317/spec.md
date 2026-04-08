# Track specification: heretic_install_strategy_20260317

## Overview
This track aims to determine and implement a safe, deterministic installation strategy for `heretic` (https://github.com/p-e-w/heretic) within the project's existing dotfiles/chezmoi/uv ecosystem.

## Functional requirements
- **Deterministic installation**: Implement a preferred installation order:
    1. uv module dependencies (pre-built binary).
    2. `chezmoi` external (pre-built binary).
    3. `mise` install (pre-built binary).
- **Environment gating**: The feature should be initially scoped to "Personal Only" environments, with clear mechanisms for enabling/disabling it.
- **Configuration management**: `heretic` configuration files must be managed and templated using `chezmoi`.

## Non-functional requirements
- **Safety**: Ensure installation doesn't interfere with existing system tools or compromise security.
- **Reproducibility**: Installation should yield the same version and state across all personal machines.

## Acceptance criteria
- [ ] `heretic` is successfully installed on personal machines using one of the specified methods.
- [ ] `heretic` configuration is correctly managed by `chezmoi`.
- [ ] The feature is gated and only active in "Personal" environments (or as configured).
- [ ] The installation method is documented and follows project standards.

## Out of scope
- Implementation for "Work" environments unless explicitly requested later.
- Custom plugins or extensions for `heretic` beyond basic configuration.
