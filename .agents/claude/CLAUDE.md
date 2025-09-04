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
```

## Key principles

- Use existing patterns before creating new ones
- Never commit secrets
- All dependencies pinned
- Guarded installation prevents corruption
- Test both personal/work profiles

## Active projects

See [.agents/scratch_zone/](.agents/scratch_zone/) for current development status and tasks.

## Scratch zone

Use `.agents/scratch_zone/` for temporary project files, notes, and task tracking during sessions. See [.agents/scratch_zone/README.md](.agents/scratch_zone/README.md) for usage guidelines.

Refer to [AGENTS.md](../AGENTS.md) for architecture, workflows, and guidelines.
