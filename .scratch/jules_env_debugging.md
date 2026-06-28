# Jules env_setup.sh bisect tracking

| Stage | Flags | Path scope | Result | Notes |
|-------|-------|------------|--------|-------|
| baseline | no apply | — | ✅ | |
| /tmp full | none | all | ✅ | |
| S1 files $HOME | `--exclude=scripts,externals` | explicit (no `~/.asdf`) | ✅ | |
| S2 files $HOME | `--exclude=scripts,externals` | all paths | ❌ | `remove_dot_asdf` deletes `~/.asdf` |
| S3 files+scripts $HOME | `--exclude=externals,remove` | all | ❌ | scripts break something |
| **A** files-only $HOME | `--exclude=scripts,externals,remove` | all | ✅ | workaround: rm .bash_profile; root cause found: modify_dot_bash_profile pollutes bash -l stdout |
| **A (clean)** files-only $HOME | `--exclude=scripts,externals,remove` | all | ✅ | PR #587 fix live; no workaround needed; bash -l stdout empty |
| **B** +externals $HOME | `--exclude=scripts,remove` | all | ✅ | binary downloads into ~/.local/bin; bash -l stdout still clean |
| **C** full apply $HOME | `--exclude=remove` | all | ✅ | **BISECT COMPLETE** — full apply minus removes works |

## Conclusion

Use `--exclude=remove` permanently.
The only thing that must never run is the `remove_` type — `remove_dot_asdf` deletes `~/.asdf` which Jules uses for Python (asdf manages Python 3.12.13).
All run_ scripts, externals, modify_ scripts, and files work correctly in Jules' Ubuntu VM.
