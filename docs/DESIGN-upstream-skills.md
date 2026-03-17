# Upstream skills: Bazel build, chezmoi deploy

Design for fetching, filtering, and deploying upstream AI tool skills from external repositories.

## Problem

Upstream skill repos (e.g., `anthropics/skills`) contain files that conflict with chezmoi's source-state conventions.
Files named `run_*.py` get executed as scripts during `chezmoi apply`.
We need a pipeline that can fetch, filter, and transform upstream skills before deployment.

## Current state

Upstream `skill-creator` is deployed via static chezmoi externals (`upstream-skills.toml`).
This works but has no filtering or transformation — it fetches the entire skill directory from a pinned GitHub archive URL.

Local skills use a separate pipeline: canonical source in `src/agents/skills/`, synced to `src/chezmoi/dot_*/skills/` via `bazel run //tools/agents:sync`, with `diff_test` drift tests.

## Target architecture

```
┌─────────────────────────────┐
│  MODULE.bazel               │
│  http_archive per upstream  │
│  repo (pinned commit)       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Bazel genrule / pkg_tar    │
│  - select skills from repo  │
│  - exclude/rename files     │
│  - produce .tar.gz per      │
│    tool (claude/cursor/     │
│    gemini)                  │
└──────────┬──────────────────┘
           │ file:// URL
           ▼
┌─────────────────────────────┐
│  chezmoi external template  │
│  .chezmoiexternals/         │
│    upstream-skills.toml.tmpl│
│  - calls `output "bazel"    │
│    "cquery" ...` to resolve │
│    archive path             │
│  - type = "archive"         │
│  - url = "file://..."       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  ~/                         │
│  .claude/skills/<skill>/    │
│  .cursor/skills/<skill>/    │
│  .gemini/skills/<skill>/    │
└─────────────────────────────┘
```

## Established patterns to follow

### CLI tools (existing)

Python CLI tools already use a `bazel build` → chezmoi deploy pattern:

1. `bazel_run_wrapper.sh` template calls `bazel build` then `bazel run --script_path`
2. `executable_*.tmpl` files reference Bazel targets
3. `.chezmoidata/local_bin_tools.toml` controls which tools are deployed

### Binary externals (existing)

Binary tools use `.chezmoiexternals/*.toml.tmpl` with version data from `.chezmoidata/`:

```toml
["bazelisk"]
type = "file"
url = {{ gitHubReleaseAssetURL "bazelbuild/bazelisk" ... | quote }}
executable = true
```

### Upstream skills (proposed)

Combine both patterns.
Bazel fetches and assembles, chezmoi templates resolve the output path:

```toml
{{- $archive := output "bazel" "cquery" "--output=files" "//tools/agents:skill_creator_archive" | trim -}}
[".claude/skills/skill-creator"]
    type = "archive"
    url = "file://{{ $archive }}"
    stripComponents = 1
```

## Implementation steps

### 1. Bazel assembly targets

Restore `http_archive` in `MODULE.bazel` for each upstream repo.
Create `pkg_tar` or `genrule` targets that:

- Select specific skills from the repo
- Exclude problematic files (e.g., `run_*.py` that conflict with chezmoi)
- Rename files if needed (e.g., prefix `run_` scripts with `script_`)
- Produce one archive per skill

```starlark
# tools/agents/upstream/BUILD.bazel
genrule(
    name = "skill_creator_archive",
    srcs = ["@anthropic_skills//:skill_creator_files"],
    outs = ["skill-creator.tar.gz"],
    cmd = """
        # Filter and package upstream skill
        tar czf $@ --transform='s/^run_/script_/' \
            -C $$(dirname $(location @anthropic_skills//:skills/skill-creator/SKILL.md))/.. \
            skill-creator/
    """,
)
```

### 2. Convert externals to template

Rename `upstream-skills.toml` → `upstream-skills.toml.tmpl`.
Use chezmoi's `output` function to call `bazel cquery` or `bazel info output_path` to resolve the archive location.

The template iterates over tools (claude, cursor, gemini) and skills, generating one external entry per combination.

### 3. Data-driven configuration

Add upstream skill pins to `.chezmoidata/`:

```toml
# .chezmoidata/upstream_skills.toml
[upstream_skills.skill-creator]
repo = "anthropics/skills"
commit = "b0cbd3df1533b396d281a6886d5132f623393a9c"
path = "skills/skill-creator"
tools = ["claude", "cursor", "gemini"]
```

This centralizes version pins and enables chezmoi templates to iterate over configured skills.

### 4. Validation as extraction

Separate frontmatter extraction from validation:

- `frontmatter.py` → parse SKILL.md into structured data (YAML/JSON frontmatter + body text)
- Extracted data enables downstream consumers: spellcheck, LLM evaluation, schema validation
- Validation becomes a consumer of extracted data, not a monolithic framework

## What this replaces

- Static `upstream-skills.toml` with hardcoded GitHub URLs (current)
- Committed upstream skill copies in `src/chezmoi/dot_*/skills/` (removed)
- `http_archive` + `upstream_skill_drift_tests` Bazel macro (removed)

## Open questions

- Should `bazel build` happen during `chezmoi apply` (lazy) or require an explicit `bazel build` first (eager)?
  Lazy is more convenient but adds build latency to `chezmoi apply`.
  Eager matches the CLI tools pattern (`bazel_run_wrapper.sh` builds on first run).
- How to handle machines without Bazel?
  Could gate upstream skills on a `.chezmoidata` flag like `local_bin_tools` does with `installation = "bazel"`.
- Should we generate per-tool archives or one archive with all tools?
  Per-tool is simpler for chezmoi externals; one archive with subdirs is simpler for Bazel.
