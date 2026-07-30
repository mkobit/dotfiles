# Integration test conventions

## Prefer chezmoi's own tooling over reinventing it

When a test needs to know what chezmoi manages, how a file is classified, or how a template renders, ask chezmoi (`chezmoi managed`, `chezmoi cat`, `chezmoi data`, `chezmoi execute-template`), don't reimplement the answer with `Path.glob` or manual template execution.
Chezmoi's own view of the source tree is authoritative; a hand-maintained filename convention can silently drift out of sync with it (a root-level-only or suffix-only glob has already missed real, in-scope files this way).
