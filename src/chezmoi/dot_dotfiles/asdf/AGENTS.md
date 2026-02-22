# asdf Version Manager

## Plugin Management

- **Define**: Add plugins to `src/.chezmoidata/asdf.toml`:
  ```toml
  plugins = [
    { name = "nodejs" },
  ]
  ```
- **Apply**: `chezmoi apply` handles plugin installation.

## Updating Version

1. Update `version` in `.chezmoidata/asdf.toml`.
2. Update platform checksums (`darwin_arm64`, etc.) from GitHub release.
3. Run `chezmoi apply`.
