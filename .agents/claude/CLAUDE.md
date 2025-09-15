# Claude context

See [AGENTS.md](../AGENTS.md) for complete project documentation.

## Quick commands

```bash
# Build personal profile
bazel build //... --//config:profile=personal

# Test and format
bazel test //...
bazel run //:format

# Install configs
bazel run //config:install_all

# DevContainer lockfile management
# Note: Lockfile auto-generates in VS Code with experimental setting enabled
```

## Key principles

- Use existing patterns before creating new ones
- Never commit secrets
- All dependencies pinned
- Guarded installation prevents corruption
- Test both personal/work profiles

## 🚨 Corporate environment constraints

**When profile = "work"**: Corporate-managed files CANNOT be wholesale replaced.

**Safe patterns:**
- `modify_` scripts → **ONLY** safe way to customize corporate `.gitconfig`, `.zshrc`, etc.
- `dot_dotfiles/` → Create your own organized directory structure  
- Private files in `~/.dotfiles/` → Full control for non-corporate managed locations

**Forbidden in work environments:**
- Never use `dot_gitconfig`, `dot_zshrc` when corporate infrastructure manages these files
- Never replace system binaries or corporate-installed tools
- `modify_` scripts are required for any file that corporate IT manages

## Active projects

See [.agents/scratch_zone/](.agents/scratch_zone/) for current development status and tasks.

## Scratch zone

Use `.agents/scratch_zone/` for temporary project files, notes, and task tracking during sessions. See [.agents/scratch_zone/README.md](.agents/scratch_zone/README.md) for usage guidelines.

Refer to [AGENTS.md](../AGENTS.md) for architecture, workflows, and guidelines.
