# Implementation plan: agency_agents_install_strategy_20260317

## Phase 1: Research and artifact discovery
- [ ] Task: Research `agency agents` release artifacts
    - [ ] Determine the latest stable version and its corresponding release artifacts.
    - [ ] Acquire the correct SHAs for the targeted binaries/archives.
    - [ ] Ensure any necessary data fields are added to `.chezmoidata.toml` for universal availability.
- [ ] Task: Conductor - User Manual Verification 'Research and artifact discovery' (Protocol in workflow.md)

## Phase 2: Configuration management
- [ ] Task: Set up `agency agents` configuration in `chezmoi`
    - [ ] Create `src/chezmoi/dot_config/agency_agents/` (or equivalent location).
    - [ ] Template the `agency agents` configuration files.
    - [ ] Verify `chezmoi` applies the configuration correctly (mocking installation if needed).
- [ ] Task: Conductor - User Manual Verification 'Configuration management' (Protocol in workflow.md)

## Phase 3: Installation strategy implementation
- [ ] Task: Implement Bazel module dependency (Option 1)
    - [ ] Explore `MODULE.bazel` for integrating `agency agents` with strict version and SHA.
    - [ ] Define the Bazel target for `agency agents` if possible.
- [ ] Task: Implement `chezmoi` external (Option 2)
    - [ ] Update `.chezmoiexternals/` to include `agency agents` download if Bazel integration is not feasible.
    - [ ] Ensure version and SHA verification are correctly specified in `.chezmoiexternals/`.
- [ ] Task: Implement `mise` fallback (Option 3)
    - [ ] Update `.chezmoidata/mise.toml` to include `agency agents` if both Bazel and `chezmoi` external are not suitable, ensuring version pinning.
- [ ] Task: Conductor - User Manual Verification 'Installation strategy implementation' (Protocol in workflow.md)

## Phase 4: Final validation and documentation
- [ ] Task: Verify the full end-to-end setup
    - [ ] Run `chezmoi apply` and verify `agency agents` installation, configuration, and SHA verification.
- [ ] Task: Document the chosen strategy
    - [ ] Update local documentation with `agency agents` setup details and update procedures.
- [ ] Task: Conductor - User Manual Verification 'Final validation and documentation' (Protocol in workflow.md)