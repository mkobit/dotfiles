# Track specification: promptfoo_install_strategy_20260317

## Overview
This track aims to determine and implement a safe, deterministic installation strategy for `promptfoo` (https://github.com/promptfoo/promptfoo) within the project's existing dotfiles/chezmoi/uv ecosystem.

## Functional requirements
- **Deterministic installation**: Implement a preferred installation order consistent with previous tool installations:
    1. uv module dependencies (first preference).
    2. `chezmoi` external (second preference).
    3. `mise` install (fallback).
- **Environment gating**: The feature should be available in all environments ("Universal").
- **Configuration management**: `promptfoo` configuration files must be managed and templated using `chezmoi`.

## Non-functional requirements
- **Safety**: Ensure installation doesn't interfere with existing system tools or compromise security.
- **Reproducibility**: Installation should yield the same version and state across all machines.

## Acceptance criteria
- [ ] `promptfoo` is successfully installed on all intended machines using one of the specified methods.
- [ ] `promptfoo` configuration is correctly managed by `chezmoi`.
- [ ] The feature is universally available across all environments.
- [ ] The installation method is documented and follows project standards.

## Out of scope
- Custom plugins or extensions for `promptfoo` beyond basic configuration.