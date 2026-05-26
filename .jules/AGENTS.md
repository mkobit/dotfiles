# Jules environment constraints

Jules runs `env_setup.sh` in a fresh Ubuntu VM (`HOME=/home/jules`, `PWD=/app`).
After the script exits, Jules runs a **post-script env-save hook** that captures the shell environment by running `bash -l -c 'env'` and parsing stdout as `KEY=VALUE` pairs.

## Critical rule: never pollute stdout of non-interactive login shells

`bash -l` is a **non-interactive login shell**.
It sources `~/.bash_profile` (and via it, any files our `modify_dot_bash_profile` injects) but does NOT set the `i` flag in `$-`.

**Any output to stdout during `~/.bash_profile` or files it sources will corrupt Jules' env-save hook.**
The hook's parser sees non-`KEY=VALUE` lines and fails silently, breaking every subsequent Jules task.

### What went wrong (2026-05)

`modify_dot_bash_profile.tmpl` creates `~/.bash_profile` where Jules never had one.
The fallback line unconditionally sourced `config.bash` in all login shells:

```bash
# BAD — runs in bash -l -c 'env', pollutes stdout
if ! type -t g &>/dev/null && [[ -f "~/.dotfiles/bash/config.bash" ]]; then
  source "~/.dotfiles/bash/config.bash"
fi
```

`config.bash` printed fzf/starship/zoxide "not found" warnings to stdout → hook failed.

### The fix

Guard all `config.bash` sourcing with `[[ $- == *i* ]]`:

```bash
# GOOD — only fires in interactive shells
if [[ $- == *i* ]] && ! type -t g &>/dev/null && [[ -f "~/.dotfiles/bash/config.bash" ]]; then
  source "~/.dotfiles/bash/config.bash"
fi
```

## General rules for modify_ scripts that touch shell RC files

- **Never** print to stdout unconditionally from `~/.bash_profile`, `~/.bashrc`, or any file they source.
- Warnings for missing tools must go to **stderr** (`>&2`) or be gated on `[[ $- == *i* ]]`.
- `modify_dot_bash_profile.tmpl` creates `~/.bash_profile` from scratch — Jules had none. Every line in it runs in `bash -l` contexts.
- `~/.bashrc` is safe because it guards itself: `case $- in *i*) ;; *) return;; esac`. But `~/.bash_profile` has no such guard.
