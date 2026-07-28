# Jules environment constraints

Jules runs `env_setup.sh` in a fresh Ubuntu VM (`HOME=/home/jules`, `PWD=/app`).
After the script exits, a post-script hook captures the shell environment via `bash -l -c 'env'`, parsing stdout as `KEY=VALUE` pairs.

## Critical rule: never pollute stdout of non-interactive login shells

`bash -l` sources `~/.bash_profile` (and anything it sources) but does not set the `i` flag in `$-`.
Any stdout output during that sourcing corrupts the hook's parser and silently breaks every subsequent Jules task.
Route missing-tool warnings to stderr, or gate them on `[[ $- == *i* ]]`.

### Real incident (2026-05)

`modify_dot_bash_profile.tmpl` created `~/.bash_profile` where Jules had none.
Its fallback unconditionally sourced `config.bash`, which printed fzf/starship/zoxide "not found" warnings to stdout:

```bash
# BAD — runs in bash -l -c 'env', pollutes stdout
if ! type -t g &>/dev/null && [[ -f "~/.dotfiles/bash/config.bash" ]]; then
  source "~/.dotfiles/bash/config.bash"
fi
```

Fixed by gating on interactivity:

```bash
# GOOD — only fires in interactive shells
if [[ $- == *i* ]] && ! type -t g &>/dev/null && [[ -f "~/.dotfiles/bash/config.bash" ]]; then
  source "~/.dotfiles/bash/config.bash"
fi
```

`~/.bashrc` self-guards (`case $- in *i*) ;; *) return;; esac`), so it's safe by default.
`~/.bash_profile` has no such guard — every line in it runs in `bash -l` contexts.
