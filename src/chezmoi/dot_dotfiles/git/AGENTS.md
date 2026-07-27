# Git config (this directory)

Pre-commit secret scanning wires through `.git_hooks.backend`, computed in `.chezmoi.toml.tmpl` from the installed git version.
Git >=2.54 uses native config-based hooks (`[hook "name"]`, event/command keys).
Older git falls back to `core.hooksPath`.

Both point at the same script, `hooks/pre-commit`.
Only `snippets/hooks.gitconfig.tmpl` branches between the two backends — the hook script itself doesn't change.

The hook renders empty (chezmoi removes it) unless `git_hooks.pre_commit.installation_method` is `chezmoi` and the `betterleaks` binary is installed.
