# Tmux configuration

Tmux configuration managed through snippets and plugins, without TPM.

## Architecture

Snippets load first (base config), then plugins execute as bash scripts.

- Config: [`config.tmux.tmpl`](config.tmux.tmpl)
- Snippets: [`snippets/`](snippets/)

## Adding plugins

1. Add data file in [`../../.chezmoidata/tmux/plugins/`](../../.chezmoidata/tmux/plugins/)
2. Add external in [`../../.chezmoiexternals/`](../../.chezmoiexternals/)
3. Run `chezmoi apply`

Plugins are pinned to specific commits and downloaded as tarballs.

## Current plugins

- [tmux-powerline](https://github.com/erikw/tmux-powerline) - Status bar

## Tmux-powerline performance

### Refresh interval impact

Status bar refresh spawns shell processes for each active segment.
Endpoint security tools like SentinelOne scan every process creation.
This causes CPU and memory pressure with frequent refresh intervals.
Current configuration uses 10-second refresh to balance responsiveness and resource usage.

### Segment performance characteristics

**Expensive segments** spawn subprocesses on every refresh:

- `disk_usage` - Runs `df` command for filesystem queries
- `battery` - Runs `ioreg` and `pmset` for hardware/power management queries
- `vcs_branch` - Runs git commands like `symbolic-ref HEAD` and `rev-parse`

**Lightweight segments** use minimal resources:

- `weather` - Caches data for 600 seconds, only fetches every 10 minutes
- `time`, `date`, `date_day` - Simple `date` command execution
- `hostname`, `pwd` - Shell built-ins or simple queries
- `mode_indicator` - Uses tmux internal state only

**Currently disabled segments:**

- `disk_usage` - Rarely changes, expensive subprocess spawning
- `battery` - Changes slowly, spawns multiple hardware query processes
- `date_day` - Merged into `date` segment format using `%a` day-of-week

### Future custom segments

Consider these patterns when authoring custom segments:

- Implement file-based caching with configurable TTL (see weather segment)
- Avoid subprocess spawning when possible
- Prefer shell built-ins over external commands
- Store expensive operation results in temporary files
- Document performance characteristics and refresh behavior

## References

- [tmux Manual](https://man.openbsd.org/tmux)
- [tmux Plugins](https://github.com/tmux-plugins/list)
- [Awesome tmux](https://github.com/rothgar/awesome-tmux)
- [tmux-powerline](https://github.com/erikw/tmux-powerline)
- [tmux-powerline Configuration](https://github.com/erikw/tmux-powerline#configuration)
