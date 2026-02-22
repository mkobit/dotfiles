# jq Configuration

## Module Management

- **Directory**: `src/dot_dotfiles/jq/` (installed to `{{ .chezmoi.destDir }}/.dotfiles/jq/`).
- **Path**: `$JQLIB` environment variable must be set to this directory.
- **Import**: `import "my_module" as my;`
