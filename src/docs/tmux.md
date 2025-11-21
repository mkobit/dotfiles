# tmux Configuration

Tmux configuration managed through snippets and plugins, without TPM.

## Architecture

Snippets load first (base config), then plugins execute as bash scripts.

- Config: [`src/dot_dotfiles/tmux/config.tmux.tmpl`](../dot_dotfiles/tmux/config.tmux.tmpl)
- Snippets: [`src/dot_dotfiles/tmux/snippets/`](../dot_dotfiles/tmux/snippets/)

## Adding Plugins

1. Add data file in [`src/.chezmoidata/tmux/plugins/`](../.chezmoidata/tmux/plugins/)
2. Add external in [`src/.chezmoiexternals/`](../.chezmoiexternals/)
3. Run `chezmoi apply`

Plugins are pinned to specific commits and downloaded as tarballs.

## Current Plugins

- [tmux-powerline](https://github.com/erikw/tmux-powerline) - Status bar

## References

- [tmux Manual](https://man.openbsd.org/tmux)
- [tmux Plugins](https://github.com/tmux-plugins/list)
- [Awesome tmux](https://github.com/rothgar/awesome-tmux)
- [tmux-powerline](https://github.com/erikw/tmux-powerline)
- [tmux-powerline Configuration](https://github.com/erikw/tmux-powerline#configuration)
