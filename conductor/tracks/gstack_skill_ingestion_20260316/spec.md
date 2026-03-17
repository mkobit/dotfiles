# Track specification: Gstack skill ingestion and deployment

# Overview
Integrate skills from the `gstack` repository into our cross-tool AI infrastructure.
We will leverage Bazel to fetch, select, rename, and transform skills from `gstack` for deployment via Chezmoi to Gemini, Claude, Cursor, and Codex agents.
This fulfills the "Bazel-powered upstream skill assembly" goal outlined in our current design documentation.

# Functional requirements
- **Upstream ingestion**: Configure `http_archive` in `MODULE.bazel` to fetch the `gstack` repository at a pinned commit.
- **Skill selection and renaming**: Implement or extend Bazel rules (e.g., in `tools/agents/`) to:
    - Select specific skills from the `gstack` archive.
    - Rename skills (directories and `SKILL.md` metadata) based on a mapping configuration.
    - Filter out files that conflict with our deployment environment (e.g., `run_*.py` files that Chezmoi might execute).
- **Transformation pipeline**:
    - Adapt skills for tool-specific formats (Gemini, Claude, Cursor, Codex).
    - Produce tool-specific archives (`.tar.gz`) for consumption by Chezmoi.
- **Chezmoi integration**:
    - Update `src/chezmoi/.chezmoiexternals/upstream-skills.toml.tmpl` to use the Bazel-produced archives via `file://` URLs.
    - Ensure the template can dynamically resolve Bazel output paths.
- **Mapping configuration**:
    - Define a mapping structure (e.g., in `src/chezmoi/.chezmoidata/agents.toml`) to control which skills are ingested and their final names.

# Non-functional requirements
- **Reproducibility**: Maintain complete reproducibility by pinning upstream sources and using Bazel for all transformations.
- **Validation**: Integrate the new pipeline with our existing Bazel validation and drift testing infrastructure.

# Acceptance criteria
- `gstack` is successfully configured as an upstream source.
- Bazel targets produce skill archives that correctly filter and rename `gstack` skills.
- Skills are successfully deployed to tool-specific directories (e.g., `~/.gemini/skills/`) and are functional.
- Renaming is verified to work as defined in the mapping configuration.

# Out of scope
- Implementation of a generalized "skill registry" for all possible remote sources (focused on `gstack` initially).
- Automatic updates of pinned commits.
