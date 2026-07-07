# Codex config data design

## Goal

Generate personal Codex config defaults from base chezmoi data without replacing mutable Codex state.

## Scope

The first managed default is Codex composer Vim mode.

The base repo also keeps Antigravity Vim mode enabled through the existing Gemini data path.

The change does not manage Codex MCP servers, plugin marketplaces, project trust, auth, or runtime state.

## Design

Add base data under `codex.tui.vim_mode_default`.

Use a chezmoi `modify_` template for `~/.codex/config.toml`.

The modify template reads the current TOML from `.chezmoi.stdin`, sets `tui.vim_mode_default`, and writes TOML back.

This preserves Stripe overlay state written by `codex mcp`, `codex plugin`, and trust workflows.

## Evidence

OpenAI's Codex config reference defines `tui.vim_mode_default` as the setting that starts the composer in Vim normal mode while preserving per-session `/vim` toggles.

Local Stripe overlay inspection found no `/etc/codex` config or requirements file on this laptop.

The overlay manages Codex extensions through CLI convergence scripts rather than a generated `config.toml`.

## Testing

Keep integration tests focused on deployment shape.

Assert `~/.codex/config.toml` exists after `chezmoi apply`.

Assert the deployed file parses as TOML.

Do not assert every key and value in the integration layer.
