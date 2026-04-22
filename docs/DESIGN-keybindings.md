# Keybinding design

Holistic key binding strategy across all platforms, terminal environments, editors, and AI tools.
When you hit a keybinding conflict, start here.

**Automation principle:** configuration is managed by chezmoi.
The fix for any keybinding issue is to update the relevant chezmoi source and run `chezmoi-personal apply` — not to manually edit files on individual machines.

---

## Quick symptom lookup

### Shift+Enter inserts a newline instead of submitting — or does nothing

| Where you are | Status | How it is managed |
|---|---|---|
| macOS Ghostty | Works natively | Nothing needed |
| macOS iTerm2 | Works natively | Nothing needed |
| Windows Terminal + WSL | **Not supported** | Use `Ctrl+J` or `\` then Enter |
| VS Code / Cursor (macOS, local or remote SSH) | Managed | `modify_keybindings.json.tmpl` deploys via `chezmoi-personal apply` |
| VS Code / Cursor (Linux / WSL) | Managed | `dot_config/Cursor/User/modify_keybindings.json.tmpl` deploys via `chezmoi-personal apply` |
| JetBrains (IntelliJ, PyCharm, etc.) | **Not supported** | Use `Ctrl+J` or `\` then Enter |

For VS Code and Cursor, the Shift+Enter keybinding lives in `keybindings.json` on the local machine.
Cursor reads this file regardless of whether you are in a remote SSH session.
Chezmoi manages it — running `chezmoi-personal apply` on the local machine is all that is needed.

### Option+Arrow (macOS) doesn't do word navigation — jumps between Zellij panes instead

Root cause: Zellij was binding `"Alt Left"` and `"Alt Right"` in `shared_except "locked"`.
Fix: arrow variants removed from `config.kdl` — deploy with `chezmoi-personal apply`.

### Option+Enter / Option+P / Option+T do nothing in Claude Code (macOS)

Root cause: terminal not configured to send Option as Meta (ESC-prefix).

| Terminal | Status | How it is managed |
|---|---|---|
| Ghostty | Configured | `macos-option-as-alt = true` in `conf.d/macos.conf` |
| VS Code / Cursor | **Gap** | `"terminal.integrated.macOptionIsMeta": true` not yet in dotfiles settings template |
| iTerm2 | Manual | Profiles → Keys → Left/Right Option → "Esc+" (not yet templated) |

### Ctrl+B in Claude Code triggers Zellij tmux mode instead of backgrounding a task

Root cause: Zellij claims `Ctrl+B` as the tmux mode entry key.
Workaround (now): enter Zellij locked mode with `Ctrl+G` before starting a Claude or Gemini session.
Fix (pending): remap Zellij's tmux mode trigger in `config.kdl` — see resolution strategy.

### Ctrl+T / Ctrl+O in Claude Code trigger Zellij mode switches

Same pattern.
`Ctrl+T` → Zellij tab mode instead of Claude Code task list.
`Ctrl+O` → Zellij session mode instead of Claude Code transcript viewer.
Workaround: Zellij locked mode (`Ctrl+G`).

### Ctrl+S doesn't do forward history search in zsh / fzf

Root cause: Zellij was claiming `Ctrl+S → SwitchToMode "Scroll"` in normal mode.
Fix: removed from `config.kdl` — deploy with `chezmoi-personal apply`.

---

## Philosophy

Key events travel through a stack of intercepting layers.
Each layer owns one modifier prefix.
A key not claimed by a layer passes through to the next one.

```
Physical key
  → OS system shortcuts              [hard constraints — do not fight]
  → Window manager                   [Ctrl+Cmd on mac / Win+key on Windows]
  → Terminal emulator                [Cmd on mac / Ctrl+Shift on Windows]
  → Terminal multiplexer (Zellij)    [Ctrl modal + Alt+letter — never arrows]
  → Shell / TUI / AI tool            [Alt+arrow, remaining Ctrl]
```

**The cardinal rule:** arrow keys with modifiers belong to the lowest layer.
Never bind `Alt+Arrow`, `Ctrl+Arrow`, or `Shift+Arrow` at the multiplexer level or above.

### Keyboard agnostic

Every binding must be typeable on a standard ANSI keyboard.
Glove80 and other ergonomic keyboards can make combinations more comfortable, but no binding should require hardware others don't have.
Use keyboard layers to reduce strain, not to enable otherwise impossible combinations.

---

## Platform stacks

### macOS — Ghostty + Zellij

```
Physical key
  → macOS system         Cmd+Tab, Cmd+Space, Ctrl+←→ (Mission Control spaces)
  → Hammerspoon          Ctrl+Cmd  ← window snapping (goal; currently Rectangle Pro native)
  → Ghostty              Cmd       ← terminal windows, tabs, custom sequences
  → Zellij               Ctrl modal + Alt+letter
  → Shell / Claude / Vim Alt+arrow (word nav), remaining Ctrl
```

Ghostty sets `macos-option-as-alt = true` (managed: `conf.d/macos.conf`).
Option+key → ESC-prefix encoding. From Zellij downward, Option and Alt are identical.

Active Ghostty bindings (managed: `conf.d/keybinds.conf`):
- `Cmd+Left` → `\x01` (line start / Ctrl+A)
- `Cmd+Right` → `\x05` (line end / Ctrl+E)
- `Cmd+Backspace` → `\x15` (kill line / Ctrl+U)

These are consumed by Ghostty and never reach Zellij or the shell.

### Windows — Windows Terminal + Ubuntu WSL + Zellij

```
Physical key
  → Windows system       Win+key, Alt+F4
  → Windows Terminal     Ctrl+Shift  ← copy, paste, tabs, splits
  → Zellij               Ctrl modal + Alt+letter
  → Shell / Claude / Vim Ctrl+Arrow (word nav), Alt+arrow, remaining Ctrl
```

`Ctrl+Shift` is consumed before the PTY — Zellij and the shell never see it.
Word navigation on Windows is `Ctrl+Arrow`, not `Alt+Arrow`.
Zellij does not bind `Ctrl+Arrow` — it passes through cleanly.
Alt is Alt natively; no Option-as-Meta translation needed.

Windows Terminal config is partially managed via `dot_local/share/fonts/` and `.chezmoidata/windows_terminal.toml` (font only).
Full Windows Terminal keybinding management is a gap — tracked in open items.

### VS Code / Cursor

**Do not run Zellij inside the IDE integrated terminal.**
The IDE's own modal shortcuts and panel keybindings conflict with Zellij.
Use Ghostty or Windows Terminal for Zellij sessions; use the IDE terminal for quick shell access only.

Managed via chezmoi:
- `Library/Application Support/{Code,Cursor}/User/modify_keybindings.json.tmpl` (macOS)
- `dot_config/{Code,Cursor}/User/modify_keybindings.json.tmpl` (Linux / WSL)

The `modify_` script merges the Shift+Enter binding idempotently into any existing `keybindings.json`.
Run `chezmoi-personal apply` on the local machine to deploy.
For remote SSH sessions, Cursor reads keybindings from the local machine — local apply is sufficient.

Not yet managed:
- `settings.json` (`terminal.integrated.macOptionIsMeta`) — tracked in open items
- `Alt+Arrow` IDE action scoping — tracked in open items

### JetBrains (IntelliJ, PyCharm, Android Studio)

Shift+Enter for multiline input is not supported — use `Ctrl+J` or `\` then Enter.
These terminals are not candidates for Zellij.
Alt+Arrow bindings may need to be scoped away from terminal focus in Keymap → Terminal.
Keybinding management for JetBrains is not yet in chezmoi.

---

## Modifier ownership table

| Modifier | macOS owner | Windows owner | Notes |
|---|---|---|---|
| `Cmd` | macOS system + Ghostty | n/a | Terminal window/tab management |
| `Ctrl+Cmd` | Hammerspoon + Rectangle | n/a | Window snapping — goal: fully version-controlled via Hammerspoon |
| `Ctrl+Shift` | n/a | Windows Terminal | Copy, paste, new tab — filtered before PTY |
| `Ctrl+letter` | Zellij modal triggers | Zellij modal triggers | Several conflict with Claude Code and readline — see below |
| `Alt+letter` | Zellij always-on nav | Zellij always-on nav | `h/j/k/l` only — never arrow variants |
| `Alt+arrow` | Shell / TUI word nav | Shell / TUI (mac compat) | On Windows, `Ctrl+Arrow` is primary |
| `Shift+arrow` | App-level selection | App-level selection | Never claim above shell layer |

---

## Full conflict map

### Zellij vs Claude Code and Gemini CLI

Both use readline-based Ctrl bindings that Zellij intercepts in normal mode.

| Key | Claude Code action | Zellij action | Severity | Resolution |
|---|---|---|---|---|
| `Ctrl+B` | Background running task | Enter tmux mode | **High** | Remap Zellij → `Ctrl+Alt+B`, or remove if tmux mode unused |
| `Ctrl+T` | Toggle task list | Enter tab mode | **High** | Remap Zellij → `Ctrl+Alt+T` |
| `Ctrl+G` | Open external editor | Toggle locked mode | **Medium** | Use `Ctrl+X Ctrl+E` as alternative in Claude Code |
| `Ctrl+O` | Toggle transcript viewer | Enter session mode | **Medium** | Remap Zellij → `Ctrl+Alt+O` |
| `Alt+Right` | Word forward | `MoveFocusOrTab "Right"` | **High** | Remove arrow variant from Zellij `config.kdl` |
| `Alt+Left` | Word back | `MoveFocusOrTab "Left"` | **High** | Remove arrow variant from Zellij `config.kdl` |
| `Ctrl+S` | — | Enter scroll mode | **Medium** | Remove from Zellij normal mode entry |
| `Ctrl+H` | readline: backward-delete | Enter move mode | Low | Backspace is equivalent |

Not claimed by Zellij (pass through to Claude Code freely):
- `Alt+B` / `Alt+F` — word navigation
- `Ctrl+R` — reverse history search
- `Ctrl+X Ctrl+E` — open in editor (readline-native; use instead of `Ctrl+G`)

### Zellij vs shell readline (zsh)

| Key | Shell action | Zellij action | Severity |
|---|---|---|---|
| `Ctrl+S` | Forward history search (fzf) | Enter scroll mode | **Medium** |
| `Ctrl+B` | Move cursor back one char | Enter tmux mode | Medium |
| `Ctrl+H` | Backward delete char | Enter move mode | Low |

### Zellij vs Vim / Neovim

No structural conflict.
Vim normal-mode navigation (`h/j/k/l`) uses plain letters — Zellij does not intercept them.
Neovim terminal escape (`Ctrl+\ Ctrl+N`) is not claimed by Zellij.
Locked mode is not required for Vim.

### Ghostty vs Zellij

No conflict.
Ghostty's `Cmd+` defaults (new tab, new window, close) are consumed before reaching Zellij.
Different modifier prefix.

### Rectangle Pro vs terminal stack

Rectangle Pro's default shortcuts use `Ctrl+Option+Arrow`.
`Ctrl+Option` is not used by Ghostty, Zellij, readline, or AI tools — no current conflict.
These shortcuts are currently managed by Rectangle Pro's own preferences and are outside dotfiles.
Goal: wire through Hammerspoon `init.lua` with `Ctrl+Cmd` prefix; managed in chezmoi.

### VS Code / Cursor — Alt+Arrow conflict

On macOS, `Alt+Left` and `Alt+Right` may be bound to IDE word or tab navigation.
This fires even when terminal panel focus is active.
Fix: scope these bindings to `editorTextFocus` only in `keybindings.json`.
Chezmoi `modify_keybindings.json.tmpl` is the right place to manage this.

---

## Resolution strategy

All fixes are applied by editing the relevant chezmoi source and running `chezmoi-personal apply`.

### Immediate — fix Alt+Arrow in Zellij

File: `src/chezmoi/dot_config/zellij/config.kdl`

Remove arrow variants from `shared_except "locked"`:
```kdl
// Remove these:
bind "Alt h" "Alt Left" { MoveFocusOrTab "Left"; }   // keep only "Alt h"
bind "Alt l" "Alt Right" { MoveFocusOrTab "Right"; }  // keep only "Alt l"
bind "Alt j" "Alt Down" { MoveFocus "Down"; }          // keep only "Alt j"
bind "Alt k" "Alt Up" { MoveFocus "Up"; }              // keep only "Alt k"
```

### Short-term — unblock shell history search

File: `src/chezmoi/dot_config/zellij/config.kdl`

Remove `Ctrl+S` as a normal-mode scroll entry trigger.
Scroll mode remains accessible from other modes.

### Medium-term — unblock Claude Code and Gemini CLI

**Option A — locked mode (viable now, no config change)**

Enter `Ctrl+G` before starting a Claude or Gemini session.
Zellij passes everything through.
`Ctrl+G` (external editor in Claude Code) is unavailable while locked — use `Ctrl+X Ctrl+E` instead.

**Option B — remap conflicting mode triggers (preferred)**

File: `src/chezmoi/dot_config/zellij/config.kdl`

| Current | Proposed | Frees |
|---|---|---|
| `Ctrl+B` → tmux mode | `Ctrl+Alt+B` or remove | `Ctrl+B` for Claude Code task backgrounding |
| `Ctrl+T` → tab mode | `Ctrl+Alt+T` | `Ctrl+T` for Claude Code task list |
| `Ctrl+O` → session mode | `Ctrl+Alt+O` | `Ctrl+O` for Claude Code transcript |
| `Ctrl+G` → locked mode | `Ctrl+Alt+G` | `Ctrl+G` for Claude Code external editor |

`Ctrl+Alt` is unused by all layers on both macOS and Windows WSL.

### Medium-term — VS Code / Cursor settings gap

File to create: `src/chezmoi/Library/Application Support/Cursor/User/modify_settings.json.tmpl` (macOS) and Linux equivalent.

Must add:
```json
"terminal.integrated.macOptionIsMeta": true
```

This enables Claude Code Option shortcuts (`Option+P`, `Option+T`, `Option+Enter`) and word navigation in the IDE terminal.

### Medium-term — Rectangle Pro via Hammerspoon

File: `src/chezmoi/dot_dotfiles/hammerspoon/init.lua`

Add `hs.hotkey.bind()` calls using the existing `RectanglePro` API with `Ctrl+Cmd` prefix.
Disable Rectangle Pro's native shortcuts in its app preferences (one-time manual step — not automatable via chezmoi).

---

## Escape hatch: Zellij locked mode

```
Ctrl+G  →  enter locked mode   (Zellij passes everything through)
Ctrl+G  →  exit locked mode
```

Zellij keeps only `Ctrl+G` itself in locked mode.
`Ctrl+G` as open-in-editor in Claude Code is unavailable while locked — use `Ctrl+X Ctrl+E`.
Use this for any TUI needing full keyboard control until Option B remapping is complete.

---

## Status bar and discoverability

A custom Claude Code status line already exists at `src/python/claude_statusline/` with a segment architecture.
The infrastructure is in place; what is missing is a tip or hint generator.

**Near-term additions to the status line:**
- A `keybinding_tips` segment that rotates through common reminders (e.g., `Ctrl+G → locked mode`, `Alt+h/j/k/l → pane nav`, `Ctrl+X Ctrl+E → open editor`)
- A `zellij_mode` segment that shows the current Zellij mode so you know when locked mode is active

**Zellij status bar (separate from Claude Code):**
Zellij supports a custom status bar plugin.
Could display the same rotating tip strip outside of Claude Code sessions.

---

## Multiline input — universal reference

| Method | Platform | Notes |
|---|---|---|
| `Ctrl+J` | Everywhere | Universal fallback — always works |
| `\` then Enter | Everywhere | Universal fallback — always works |
| `Shift+Enter` | Ghostty, iTerm2, WezTerm, Kitty, Warp, Apple Terminal | Native support, no setup |
| `Shift+Enter` | VS Code, Cursor | Managed via chezmoi `modify_keybindings.json.tmpl` |
| `Shift+Enter` | Windows Terminal, JetBrains | Not supported — use `Ctrl+J` |
| `Option+Enter` | macOS (Ghostty) | Requires Option-as-Meta; already configured |

---

## Open items

### Chezmoi changes needed

- [x] **Immediate:** Remove `Alt+arrow` from Zellij `shared_except "locked"` (`config.kdl`)
- [x] **Short-term:** Remove `Ctrl+S` as Zellij normal-mode scroll entry trigger (`config.kdl`)
- [ ] **Medium:** Remap Zellij `Ctrl+B/T/O/G` to `Ctrl+Alt` variants (`config.kdl`)
- [ ] **Medium:** Create `modify_settings.json.tmpl` for VS Code and Cursor — add `terminal.integrated.macOptionIsMeta: true`
- [ ] **Medium:** Extend `modify_keybindings.json.tmpl` to scope `Alt+Arrow` away from terminal focus in VS Code/Cursor
- [ ] **Medium:** Add Hammerspoon hotkey bindings for Rectangle Pro (`Ctrl+Cmd` prefix) to `init.lua`
- [ ] **Long-term:** Expand Windows Terminal config in chezmoi beyond font (add keybindings template)

### Status line additions

- [ ] **Medium:** Add `keybinding_tips` rotating segment to `src/python/claude_statusline/`
- [ ] **Medium:** Add `zellij_mode` segment so locked mode is visible in the status line

### One-time manual steps (not automatable)

- [ ] Disable Rectangle Pro's native global shortcuts in app preferences (after Hammerspoon bindings are wired)
