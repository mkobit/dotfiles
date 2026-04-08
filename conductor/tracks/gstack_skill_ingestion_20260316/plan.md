# Implementation plan: Gstack skill ingestion and deployment

# Phase 1: Upstream ingestion and basic target
- [ ] Task: Configure `gstack` as a uv upstream
    - [ ] Update `MODULE.uv` to include `http_archive` for `gstack`.
    - [ ] Pin `gstack` to a specific commit.
    - [ ] Verify `uv query` can see the `gstack` repository.
- [ ] Task: Define a prototype skill ingestion target
    - [ ] Create a preliminary `gstack_skill` target in `tools/agents/BUILD.uv`.
    - [ ] Implement a basic `genrule` to extract a single skill from the `gstack` archive.
    - [ ] Verify the skill is extracted correctly to `uv-bin`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Upstream Ingestion & Basic Target' (Protocol in workflow.md)

# Phase 2: Transformation and renaming logic
- [ ] Task: Implement skill selection and renaming in uv
    - [ ] Write unit tests for renaming and filtering logic in `tools/agents/rules.bzl`.
    - [ ] Implement `rename_skill` and `filter_skill_files` functions in Starlark.
    - [ ] Support metadata (`SKILL.md`) transformation and renaming.
- [ ] Task: Generate tool-specific archives
    - [ ] Create targets to produce `.tar.gz` archives for Gemini, Claude, Cursor, and Codex.
    - [ ] Ensure archives contain the correct set of selected and renamed skills.
    - [ ] Verify archive contents match expectations.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Transformation & Renaming Logic' (Protocol in workflow.md)

# Phase 3: Chezmoi integration and deployment
- [ ] Task: Update Chezmoi external templates
    - [ ] Modify `src/chezmoi/.chezmoiexternals/upstream-skills.toml.tmpl`.
    - [ ] Implement `uv cquery` resolution for tool-specific archives within the template.
    - [ ] Update `src/chezmoi/.chezmoidata/agents.toml` with the initial mapping configuration.
- [ ] Task: Verify end-to-end deployment
    - [ ] Run `chezmoi apply` to deploy a renamed skill from `gstack`.
    - [ ] Verify the skill appears in tool-specific directories (e.g., `~/.gemini/skills/`) with the correct name.
    - [ ] Ensure no conflicting files (e.g., `run_*.py`) are deployed.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Chezmoi Integration & Deployment' (Protocol in workflow.md)

# Phase 4: Finalization and drift testing
- [ ] Task: Extend drift tests for upstream skills
    - [ ] Add `diff_test` to ensure deployed skills stay in sync with the uv transformation.
    - [ ] Update CI configuration to include the new ingestion pipeline.
- [ ] Task: Document the ingestion process
    - [ ] Update `docs/DESIGN-upstream-skills.md` with the finalized architecture.
    - [ ] Provide clear instructions for adding or renaming new skills from `gstack`.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Finalization & Drift Testing' (Protocol in workflow.md)
