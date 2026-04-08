# Track specification: agency_agents_install_strategy_20260317

## Overview
This track aims to determine and implement a safe, deterministic installation strategy for `agency agents` (https://github.com/msitarzewski/agency-agents) within the project's existing dotfiles/chezmoi/uv ecosystem, with a strict requirement for version pinning and SHAs.

## Functional requirements
- **Deterministic installation**: Implement a preferred installation order consistent with previous tool installations, enforcing strict version pinning and SHA verification:
    1. uv module dependencies (first preference).
    2. `chezmoi` external (second preference).
    3. `mise` install (fallback).
- **Environment gating**: The feature should be available in all environments ("Universal").
- **Configuration management**: `agency agents` configuration files must be managed and templated using `chezmoi`.

## Non-functional requirements
- **Safety**: Ensure installation doesn't interfere with existing system tools or compromise security. Validating SHAs is required to guarantee artifact integrity.
- **Reproducibility**: Installation should yield the exact same version and state across all machines due to strict versioning.

## Acceptance criteria
- [ ] `agency agents` is successfully installed on all intended machines using one of the specified methods.
- [ ] The installed artifact's version is explicitly pinned and its SHA is verified during the installation process.
- [ ] `agency agents` configuration is correctly managed by `chezmoi`.
- [ ] The feature is universally available across all environments.
- [ ] The installation method is documented and follows project standards.

## Out of scope
- Custom plugins or extensions for `agency agents` beyond basic configuration.