# tmux Configuration

Tmux configuration managed through snippets and plugins, without TPM.

## Architecture

**Snippets** load first (base config), then **plugins** execute as bash scripts (can override).

- Snippets: `src/dot_dotfiles/tmux/snippets/*.tmux`
- Plugins: `src/.chezmoiexternals/<plugin>.toml.tmpl`
- Main: `src/dot_dotfiles/tmux/config.tmux.tmpl`

## Adding Plugins

1. Create data file at `src/.chezmoidata/tmux/plugins/<plugin-name>.toml`:
   ```toml
   [tmux.plugins.<plugin-name>]
   enabled = true
   commit = "abc123..."
   ```

2. Create external at `src/.chezmoiexternals/<plugin-name>.toml.tmpl`:
   ```toml
   {{- $plugin := index .tmux.plugins "<plugin-name>" -}}
   {{- if $plugin.enabled -}}
   [".dotfiles/tmux/plugins/<plugin-name>"]
       type = "archive"
       url = "https://github.com/author/plugin/archive/{{ $plugin.commit }}.tar.gz"
       exact = true
       stripComponents = 1
   {{- end -}}
   ```

3. Run: `chezmoi apply`

## Current Plugins

- [tmux-powerline](https://github.com/erikw/tmux-powerline) - Status bar

## References

- [tmux Manual](https://man.openbsd.org/tmux)
- [tmux Plugins](https://github.com/tmux-plugins/list)
- [Awesome tmux](https://github.com/rothgar/awesome-tmux)
- [tmux-powerline Config](https://powerline.readthedocs.io/en/latest/configuration.html)
