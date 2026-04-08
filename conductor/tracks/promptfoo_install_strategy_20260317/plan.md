# Implementation plan: promptfoo_install_strategy_20260317

## Phase 1: Research and environment readiness
- [ ] Task: Research `promptfoo` distribution formats
    - [ ] Determine if `promptfoo` offers pre-built binaries or easily installable packages.
    - [ ] Ensure any necessary data fields are added to `.chezmoidata.toml` for universal availability.
- [ ] Task: Conductor - User Manual Verification 'Research and environment readiness' (Protocol in workflow.md)

## Phase 2: Configuration management
- [ ] Task: Set up `promptfoo` configuration in `chezmoi`
    - [ ] Create `src/chezmoi/dot_config/promptfoo/` (or equivalent location).
    - [ ] Template the `promptfoo` configuration files.
    - [ ] Verify `chezmoi` applies the configuration correctly (mocking installation if needed).
- [ ] Task: Conductor - User Manual Verification 'Configuration management' (Protocol in workflow.md)

## Phase 3: Installation strategy implementation
- [ ] Task: Implement uv module dependency (Option 1)
    - [ ] Explore `MODULE.uv` for integrating `promptfoo`.
    - [ ] Define the uv target for `promptfoo` if possible.
- [ ] Task: Implement `chezmoi` external (Option 2)
    - [ ] Update `.chezmoiexternals/` to include `promptfoo` download if uv integration is not feasible.
- [ ] Task: Implement `mise` fallback (Option 3)
    - [ ] Update `.chezmoidata/mise.toml` to include `promptfoo` if both uv and `chezmoi` external are not suitable.
- [ ] Task: Conductor - User Manual Verification 'Installation strategy implementation' (Protocol in workflow.md)

## Phase 4: Final validation and documentation
- [ ] Task: Verify the full end-to-end setup
    - [ ] Run `chezmoi apply` and verify `promptfoo` installation and configuration.
- [ ] Task: Document the chosen strategy
    - [ ] Update local documentation with `promptfoo` setup details.
- [ ] Task: Conductor - User Manual Verification 'Final validation and documentation' (Protocol in workflow.md)