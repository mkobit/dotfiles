# Chezmoi Integration Project Plan

## Overview
Integrate chezmoi as the dotfile deployment engine while preserving Bazel's validation, testing, and reproducibility benefits. Bazel builds and validates hermetically; chezmoi deploys on target machines.

## Architecture Vision
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Bazel Build     │───▶│ Chezmoi Source   │───▶│ Target Machine  │
│ (hermetic)      │    │ (generated)      │    │ (chezmoi only)  │
│                 │    │                  │    │                 │
│ • Build configs │    │ • dot_gitconfig  │    │ • ~/.gitconfig  │
│ • Validate      │    │ • dot_zshrc.tmpl │    │ • ~/.zshrc      │
│ • Test outputs  │    │ • .chezmoidata/  │    │ • ~/.tmux.conf  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Key principle**: Bazel never touches target filesystem. Chezmoi never does validation.

## Project Phases

### Phase 1: Foundation (Days 1-3)
**Goal**: Establish chezmoi toolchain and hermetic validation rules

#### 1.1 Chezmoi Toolchain
- [ ] Pin chezmoi version in `WORKSPACE` or `MODULE.bazel`
- [ ] Create `toolchains/chezmoi/BUILD.bazel` with toolchain definition
- [ ] Test hermetic chezmoi execution in Bazel sandbox

#### 1.2 Base Rules
- [ ] Create `rules/chezmoi/defs.bzl` with core rules:
  - `chezmoi_source_tree`: Generate source directory structure
  - `chezmoi_validate`: Run `chezmoi apply --dry-run` hermetically
  - `chezmoi_test`: Validate generated config content
- [ ] Create `rules/chezmoi/private/` for implementation details

#### 1.3 Testing Infrastructure
- [ ] Hermetic test environment (temp directories)
- [ ] Config validation framework reusable across tools
- [ ] Profile switching test harness

### Phase 2: Proof of Concept - Single Tool (Days 4-6)
**Goal**: Complete git config migration as working example

#### 2.1 Git Config Conversion
- [ ] Convert `src/git/configs/` templates to chezmoi format
- [ ] Create `.chezmoidata/` profile data structure
- [ ] Generate `dot_gitconfig.tmpl` preserving existing logic
- [ ] Maintain personal/work profile separation

#### 2.2 Bazel Integration
- [ ] Add `src/git:chezmoi_source` target
- [ ] Add `src/git:validate_chezmoi` test target
- [ ] Verify hermetic builds produce identical outputs
- [ ] Test profile switching in isolation

#### 2.3 Validation Preservation
- [ ] Port existing git config validation to chezmoi output
- [ ] Cross-platform compatibility tests
- [ ] Profile-specific validation rules

### Phase 3: Incremental Tool Migration (Days 7-11)
**Goal**: Migrate remaining tools one at a time

#### 3.1 Migration Order
**Priority**: zsh → tmux → vim → jq → hammerspoon

For each tool:
- [ ] Convert templates maintaining existing functionality
- [ ] Add chezmoi-specific Bazel targets
- [ ] Validate against current Bazel output
- [ ] Update profile data as needed

#### 3.2 Advanced Features
- [ ] Machine-specific conditionals
- [ ] Complex template logic migration
- [ ] Multi-file tool configurations
- [ ] Cross-tool dependencies

### Phase 4: Production System (Days 12-14)
**Goal**: Complete working system with deployment workflow

#### 4.1 Complete Build System
- [ ] Top-level `//chezmoi:all` target for full source tree
- [ ] Profile-aware build configuration
- [ ] Comprehensive validation suite
- [ ] CI integration and testing

#### 4.2 Deployment Workflow
- [ ] Target machine setup documentation
- [ ] Source tree distribution mechanism
- [ ] Rollback and recovery procedures
- [ ] Multi-machine deployment testing

#### 4.3 Documentation & Migration
- [ ] Update CLAUDE.md with new workflows
- [ ] Create deployment runbooks
- [ ] Archive old installation rules
- [ ] Performance and complexity comparison

## Technical Design

### Rule Interface
```python
chezmoi_source_tree(
    name = "git_source",
    srcs = ["//src/git:configs"],
    profile_data = "//config:profile_data",
)

chezmoi_validate(
    name = "git_validate", 
    source_tree = ":git_source",
    validation_script = "//tools:validate_git_config",
)
```

### Workflow
```bash
# Development (Bazel machine)
bazel build //chezmoi:all --//config:profile=work
bazel test //chezmoi:validate_all

# Target machine (chezmoi only)
chezmoi init --source=./bazel-bin/chezmoi/source_tree
chezmoi apply
```

### Profile Data
```yaml
# .chezmoidata/config.yaml
profile: "{{ .profile | default "personal" }}"
git:
  user_email: >-
    {{- if eq .profile "work" -}}
    work@company.com
    {{- else -}}
    personal@example.com
    {{- end }}
```

## Success Criteria
- [ ] All tools migrated with feature parity
- [ ] Hermetic validation passes in CI
- [ ] Profile switching works correctly
- [ ] Target deployment < 30 seconds
- [ ] Zero dependency on Bazel for target machines
- [ ] Rollback capability preserved

## Risk Mitigation
- **Incremental approach**: One tool at a time with validation
- **Output comparison**: Bazel vs chezmoi validation at each step
- **Backup strategy**: Preserve existing Bazel rules until complete
- **Isolated testing**: All validation in hermetic environments

## Phase 1 Starting Point
Begin with chezmoi toolchain setup and basic rule framework. Each subsequent phase builds incrementally with full validation before proceeding.
