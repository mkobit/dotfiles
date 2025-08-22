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

Refer to [AGENTS.md](../AGENTS.md) for architecture, workflows, and guidelines.
