# Implementation plan - CI caching improvement

## Phase 1: Research and baseline
- [ ] Task: Audit current CI workflow and identify caching gaps
- [ ] Task: Establish baseline CI runtime for full and incremental builds
- [ ] Task: Conductor - User manual verification 'Phase 1: Research and baseline' (Protocol in workflow.md)

## Phase 2: Bazel caching optimization
- [ ] Task: Research and select optimal Bazel-GHA caching strategy (e.g., `actions/cache` for `~/.cache/bazel`)
- [ ] Task: Implement caching for Bazel repository rules and external modules in `setup-bazel-common`
- [ ] Task: Configure Bazel flags for optimal disk cache usage in CI (`--disk_cache`)
- [ ] Task: Verify Bazel cache hits in CI logs
- [ ] Task: Conductor - User manual verification 'Phase 2: Bazel caching optimization' (Protocol in workflow.md)

## Phase 3: Python dependency caching
- [ ] Task: Identify storage locations for Bazel-managed Python dependencies
- [ ] Task: Implement caching for Python toolchains and libraries in CI
- [ ] Task: Verify Python cache hits and reduced download times
- [ ] Task: Conductor - User manual verification 'Phase 3: Python dependency caching' (Protocol in workflow.md)

## Phase 4: Refinement and validation
- [ ] Task: Optimize cache keys to balance hit rate and freshness
- [ ] Task: Conduct final performance benchmark against baseline
- [ ] Task: Document caching strategy and maintenance procedures in `AGENTS.md` or CI docs
- [ ] Task: Conductor - User manual verification 'Phase 4: Refinement and validation' (Protocol in workflow.md)
