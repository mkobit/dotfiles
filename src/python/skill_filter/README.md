# skill-filter

Archive-to-archive filter used by chezmoi externals to deploy selected AI skills.

## Contract

Reads a gzipped tar archive on stdin and writes a plain tar archive on stdout.
Chezmoi downloads a pinned upstream repository archive, pipes it through this tool via `filter.command`, and extracts the result to the external's target directory.

```sh
python3 skill_filter/main.py --strip-components 1 --select skills/brainstorming:. < repo.tar.gz > skill.tar
```

## Constraints

This module is stdlib-only and self-contained on purpose.
It runs via system `python3` at chezmoi apply time, before uv or mise are installed, and is invoked by file path from `{{ .chezmoi.workingTree }}/src/python/skill_filter/skill_filter/main.py`.
Overlay environments that rsync this repo into a combined chezmoi source tree must include `src/python/skill_filter/` for skill externals to work.
Do not add runtime dependencies or intra-package imports.

## Selection semantics

- `--select SRC[:DEST]` is repeatable; `SRC` is a directory path inside the prefix-stripped archive.
- `DEST` defaults to the basename of `SRC`; a `DEST` of `.` re-roots the subtree contents at the output root (single selection only).
- `--strip-components N` strips leading path components before matching (default 1, the GitHub archive top directory).

## Safety

Members with absolute paths or `..` components abort the run with a non-zero exit.
Symlink, hardlink, and special members are skipped with a warning on stderr.
File ownership is normalized to root in the output.
Output entries are sorted by name for deterministic results.

## Extension point

The archive-in/archive-out contract is the seam for future per-tool content transformation (the rulette idea).
A transforming filter can replace this tool without changing the chezmoi external structure.

## Development

Tested through the uv workspace; the deployed artifact is just this file tree, nothing is installed.

```sh
uv run pytest src/python/skill_filter
uv run ruff check src/python/skill_filter
```
