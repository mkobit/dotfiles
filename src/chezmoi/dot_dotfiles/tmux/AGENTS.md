# Tmux Configuration

## Architecture

- **No TPM**: We do NOT use Tmux Plugin Manager.
- **Plugins**: Managed as pinned git commits in `.chezmoidata/tmux/plugins/` and downloaded via `.chezmoiexternals/`.
- **Loading**: Snippets load first, then plugins execute as scripts.

## Performance Constraints

- **Refresh Interval**: 10 seconds (avoids EDR/CPU spikes).
- **Expensive Segments** (e.g., `disk_usage`, `battery`): DISABLED by default to prevent subprocess spawning.
- **Lightweight Segments**: Preferred (cached or shell built-ins).
