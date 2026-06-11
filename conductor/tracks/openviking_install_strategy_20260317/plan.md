# Implementation plan: openviking_install_strategy_20260317

## Phase 1: Research and environment gating
- [ ] Task: Research and define `openviking` environment gating
    - [ ] Identify `chezmoi` data fields for environment classification (personal vs work)
    - [ ] Create a feature flag/data entry in `.chezmoidata.toml` for `openviking`
- [ ] Task: Conductor - User Manual Verification 'Research and environment gating' (Protocol in workflow.md)

## Phase 2: Configuration management
- [ ] Task: Set up `openviking` configuration in `chezmoi`
    - [ ] Create `src/chezmoi/dot_config/openviking/` (or equivalent)
    - [ ] Template the `openviking` configuration files
    - [ ] Verify `chezmoi` applies the configuration correctly (mocking installation if needed)
- [ ] Task: Conductor - User Manual Verification 'Configuration management' (Protocol in workflow.md)

## Phase 3: Installation strategy implementation
- [ ] Task: Implement Bazel module dependency (Option 1)
    - [ ] Explore `MODULE.bazel` for pre-built binary or source archive integration
    - [ ] Define the Bazel target for `openviking`
- [ ] Task: Implement `chezmoi` external (Option 2)
    - [ ] Update `.chezmoiexternals/` to include `openviking` download
    - [ ] Ensure the external download is only active for personal environments
- [ ] Task: Implement `mise` fallback (Option 3)
    - [ ] Update `.chezmoidata/mise.toml` to include `openviking`
- [ ] Task: Conductor - User Manual Verification 'Installation strategy implementation' (Protocol in workflow.md)

## Phase 4: Final validation and documentation
- [ ] Task: Verify the full end-to-end setup
    - [ ] Run `chezmoi apply` and verify `openviking` installation and config
    - [ ] Test the gating mechanism (enable/disable `openviking` in config)
- [ ] Task: Document the chosen strategy
    - [ ] Update local documentation with `openviking` setup details
- [ ] Task: Conductor - User Manual Verification 'Final validation and documentation' (Protocol in workflow.md)