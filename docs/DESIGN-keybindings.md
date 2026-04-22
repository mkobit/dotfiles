# Keybinding design

Configuration is managed by chezmoi.
Fix any keybinding issue by updating the chezmoi source and running `chezmoi-personal apply`.

---

## Layer ownership

```
Physical key
  → macOS system         Cmd+Tab, Cmd+Space, Ctrl+←→ (Mission Control)
  → Ghostty              Cmd  (terminal windows/tabs)
  → Zellij               Ctrl modal + Alt+h/j/k/l
  → Shell / TUI / AI     Alt+Arrow (word nav), remaining Ctrl
```

**Rule:** never bind `Alt+Arrow` or `Ctrl+Arrow` at the multiplexer layer or above.

---

## Zellij quick reference

| Key | Action |
|---|---|
| `Ctrl+G` | Toggle locked mode (full passthrough — use when Claude/Gemini needs all keys) |
| `Ctrl+P` | Pane mode |
| `Ctrl+T` | Tab mode |
| `Ctrl+O` | Session mode |
| `Ctrl+N` | Resize mode |
| `Ctrl+H` | Move mode |
| `Ctrl+S` | Scroll mode |
| `Alt+h/j/k/l` | Navigate panes (always-on, all modes except locked) |
| `Alt+i/o` | Move tab left/right |

Locked mode keeps only `Ctrl+G`.
Use `Ctrl+X Ctrl+E` as the open-in-editor alternative in Claude Code when locked.

---

## Known conflicts

| Key | Zellij | Claude Code / shell | Resolution |
|---|---|---|---|
| `Alt+Arrow` | Was pane nav | Word navigation | **Fixed** — arrow variants removed from `config.kdl` |
| `Ctrl+B` | Was tmux mode | Background task / cursor back | **Fixed** — tmux mode removed from `config.kdl` |
| `Ctrl+T` | Tab mode | Claude task list | Use locked mode (`Ctrl+G`) |
| `Ctrl+O` | Session mode | Claude transcript | Use locked mode |

---

## Managed files

| File | What it controls |
|---|---|
| `src/chezmoi/dot_config/zellij/config.kdl` | All Zellij keybindings |
| `src/chezmoi/conf.d/macos.conf` (Ghostty) | `macos-option-as-alt = true` |
| `src/chezmoi/conf.d/keybinds.conf` (Ghostty) | `Cmd+Left/Right/Backspace` → readline sequences |
| `Library/Application Support/{Code,Cursor}/User/modify_keybindings.json.tmpl` | Shift+Enter in VS Code/Cursor (macOS) |
| `dot_config/{Code,Cursor}/User/modify_keybindings.json.tmpl` | Shift+Enter in VS Code/Cursor (Linux/WSL) |

---

## Multiline input

| Method | Works in |
|---|---|
| `Ctrl+J` | Everywhere (universal fallback) |
| `\` then Enter | Everywhere (universal fallback) |
| `Shift+Enter` | Ghostty, iTerm2, VS Code/Cursor (managed via chezmoi) |
| `Option+Enter` | macOS Ghostty (Option-as-Meta already configured) |
| `Shift+Enter` | Windows Terminal, JetBrains — **not supported** |

---

## Open items

- [ ] `terminal.integrated.macOptionIsMeta: true` in VS Code/Cursor `settings.json` (enables Option shortcuts in IDE terminal)
- [ ] Windows Terminal keybinding template in chezmoi
- [ ] Rectangle Pro → Hammerspoon (`Ctrl+Cmd` prefix)
