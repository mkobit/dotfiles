# ZSH Keybinding Audit - Phase 1 Results

## Environment Tested
- **Date**: $(date)
- **Context**: VS Code terminal + tmux
- **Shell**: /bin/zsh
- **Terminal**: vscode (screen-256color)
- **Oh-My-Zsh**: ✅ Loaded (/Users/mikekobit/.oh-my-zsh)
- **FZF**: ✅ Available
- **Zoxide**: ✅ Available

## Critical Findings

### 1. Configuration Loading Order Issue ⚠️
**Problem**: Vi mode is being overridden by oh-my-zsh
- Our `performance.zsh` sets `bindkey -v`
- `oh-my-zsh.zsh` loads oh-my-zsh
- Oh-my-zsh resets keymap back to emacs mode
- **Result**: Shell runs in emacs mode despite vi mode configuration

**Evidence**:
- HISTSIZE=100000 (our config loading ✅)
- KEYTIMEOUT=1 (our config loading ✅)
- Current keymap: emacs (vi mode overridden ❌)

### 2. Established Working Bindings ✅
These are confirmed working in current environment:
- **Ctrl-R**: FZF history search
- **Ctrl-T**: FZF file finder
- **Alt-C**: FZF directory navigation

### 3. Load Order Dependencies
Current file concatenation order (from BUILD.bazel):
```
oh-my-zsh.zsh     # Loads oh-my-zsh (resets to emacs mode)
performance.zsh   # Sets vi mode (gets overridden)
fzf.zsh          # Works fine
zoxide.zsh       # Works fine
```

## Immediate Actions Required

### Fix 1: Vi Mode Loading Order
**Options**:
A. Move `bindkey -v` to end of performance.zsh (after all oh-my-zsh loading)
B. Set vi mode in oh-my-zsh.zsh after sourcing oh-my-zsh
C. Configure oh-my-zsh to not override keymap

**Recommendation**: Option B - Set vi mode after oh-my-zsh loads

### Fix 2: Environment-Specific Testing Needed
Current test was in VS Code terminal + tmux. Need to test in:
- [ ] iTerm2 (without tmux)
- [ ] iTerm2 + tmux
- [ ] Terminal.app + tmux
- [ ] Linux terminal
- [ ] WSL

## Phase 2 Preparation

### Safe Keybindings (Confirmed Working)
- Ctrl-R, Ctrl-T, Alt-C (FZF)
- Standard arrow keys for history
- Backspace, Delete (default)

### Potentially Safe Additions (Need Testing)
- Ctrl-P/N (history navigation) - might conflict with tmux
- Ctrl-W (kill word) - might conflict with terminal/browser
- Ctrl-H (backspace) - usually safe
- Ctrl-A/E (line begin/end) - usually safe but might conflict with tmux prefix

### High-Risk Bindings (Avoid for Now)
- Alt + any key (terminal emulator conflicts)
- Ctrl-B (tmux default prefix)
- Ctrl-Z (suspend - system level)

## Next Steps
1. Fix vi mode loading order
2. Test in iTerm2 + tmux (primary environment)
3. Establish baseline safe keybindings
4. Document per-environment differences
5. Create conflict-free enhancement strategy
