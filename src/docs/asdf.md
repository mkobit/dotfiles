# asdf version manager

asdf is a universal version manager for managing multiple runtime versions with a single CLI tool.

## Quick reference

**Installation**: Binary managed via `.chezmoiexternals` → `~/.local/bin/asdf`
**Configuration**: Plugin list in `.chezmoidata/asdf.toml`
**Shell integration**: Managed via `dot_dotfiles/asdf/asdf.sh.tmpl` → sourced in `.zshrc`
**Tool versions**: Managed per-project using `.tool-versions` files in project directories

## Configuration files

### Plugin configuration
- **Location**: `.chezmoidata/asdf.toml`
- **Purpose**: Defines asdf version, enabled plugins, and binary checksums
- **Managed by**: Checked into repository, synced by `run_once_install-asdf.sh.tmpl`

## How it works

1. **Binary installation**: The asdf binary is downloaded via chezmoi externals from GitHub releases
2. **Plugin management**: The `run_once_install-asdf.sh.tmpl` script syncs plugins:
   - Installs missing plugins from the configured list
   - Removes plugins not in the configured list
   - Uses colored logging to show installation progress
3. **Shell integration**: The asdf shim directory is added to PATH via sourced shell script
4. **Version management**: Tool versions are managed per-project using `.tool-versions` files

## Plugin configuration

All plugins use **official shortnames** from the [asdf-plugins registry](https://github.com/asdf-vm/asdf-plugins). When you run `asdf plugin add <name>`, asdf automatically resolves the shortname to the official plugin repository.

Example plugins configured:
- `nodejs` → https://github.com/asdf-vm/asdf-nodejs
- `python` → https://github.com/danhper/asdf-python
- `java` → https://github.com/halcyon/asdf-java
- `golang` → https://github.com/asdf-community/asdf-golang
- `rust` → https://github.com/code-lever/asdf-rust

**Note**: Custom plugin URLs are not currently supported. All plugins must be available in the official shortname registry.

## Feature control

asdf installation is controlled by the `asdf.enabled` flag in `.chezmoidata/asdf.toml`.

## Adding a new plugin

1. Add the plugin to the `plugins` array in `.chezmoidata/asdf.toml`:
   ```toml
   plugins = [
     { name = "nodejs" },
     { name = "your-new-plugin" },
   ]
   ```
2. Run `chezmoi apply` to install the plugin
3. Install tool versions per-project:
   - Create a `.tool-versions` file in your project directory
   - Add your desired version: `your-new-plugin 1.2.3`
   - Run `asdf install` in that directory to install the version

## Managing tool versions

Tool versions are **not** managed globally by this dotfiles setup. Instead:

- Each project should have its own `.tool-versions` file
- Run `asdf install` in a project directory to install versions for that project
- This approach keeps version dependencies explicit and project-specific

## Updating asdf version

1. Check the latest release at https://github.com/asdf-vm/asdf/releases
2. Update `version` in `.chezmoidata/asdf.toml`
3. Update the platform checksums in `[asdf.checksums]` section:
   - Find SHA256 hashes on the GitHub release page
   - Update `darwin_arm64`, `darwin_amd64`, `linux_amd64`, `linux_arm64`
4. Run `chezmoi apply` to download and verify the new binary

## References

- [asdf documentation](https://asdf-vm.com/guide/getting-started.html)
- [asdf plugin management](https://asdf-vm.com/manage/plugins.html)
- [asdf GitHub releases](https://github.com/asdf-vm/asdf/releases)
- [asdf plugins registry](https://github.com/asdf-vm/asdf-plugins)
