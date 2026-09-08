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
It must run on the system `python3` at chezmoi apply time, since uv and mise are not installed yet on a fresh machine, and it is invoked by file path from `{{ .chezmoi.workingTree }}/src/python/skill_filter/skill_filter/main.py`.
That is a floor, not the interpreter actually used: `resolve-interpreter.sh` prefers a uv- or mise-managed 3.11+ when one exists because those start faster, and falls back to the system interpreter otherwise.
Keeping the 3.8 contract is what makes that fallback safe — every interpreter it can pick behaves identically, so the choice never changes output.
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

The same executable can reconcile managed AI skill roots from a strict newline manifest on stdin.
Entries are destination-relative direct children of `.claude/skills`, `.codex/skills`, `.cursor/skills`, or `.gemini/antigravity-cli/skills`.
It validates both the desired and prior state before deleting stale recorded directories, then atomically replaces the state manifest.

```sh
/usr/bin/python3 -S skill_filter/main.py cleanup-skill-roots \
  --dest-dir /target \
  --state-manifest /target/.local/state/dotfiles/ai-skill-roots.manifest <<'EOF'
.codex/skills/brainstorming
EOF
```

The `reconcile-plugins` command reads a versioned JSON desired-state plan from stdin.
The ownership file must be strictly beneath `<dest-dir>/.local/state/dotfiles/`.
Each resource provides stable identity and fingerprint fields plus exact install and uninstall argv arrays.
Plugin resources also provide verification argv and expected skill identities.
Verification commands must emit either a JSON skill array or an object with a `skills` array.
An unowned plugin resource may set `"adopt": true` to verify an existing installation and record ownership without running its install command.
Adoption is limited to plugins and succeeds only when verification returns exactly `expected_skills`.
Every stale root removed by `legacy_cleanup` must have one `skill_mappings` entry naming a desired plugin and one of that plugin's expected skills.

```sh
/usr/bin/python3 -S skill_filter/main.py reconcile-plugins \
  --dest-dir /target \
  --ownership-file /target/.local/state/dotfiles/agent-plugin-ownership.json <<'EOF'
{
  "version": 1,
  "resources": [
    {
      "kind": "plugin",
      "host": "claude",
      "id": "bridge@dotfiles",
      "fingerprint": "sha256:0123456789abcdef",
      "install": ["claude", "plugin", "install", "bridge@dotfiles"],
      "uninstall": ["claude", "plugin", "uninstall", "bridge@dotfiles"],
      "verify": ["plugin-skill-adapter", "claude", "bridge@dotfiles"],
      "expected_skills": ["brainstorming"],
      "adopt": true
    }
  ],
  "skill_mappings": [
    {
      "legacy_root": ".claude/skills/brainstorming",
      "host": "claude",
      "plugin": "bridge@dotfiles",
      "skill": "brainstorming"
    }
  ],
  "legacy_cleanup": null
}
EOF
```

The converger installs marketplaces before plugins, verifies every desired plugin, performs deferred legacy cleanup, uninstalls obsolete owned plugins before marketplaces, and atomically replaces ownership state.
Resources absent from ownership state are unmanaged and are never removed.

## Extension point

The archive-in/archive-out contract is the seam for future per-tool content transformation (the rulette idea).
A transforming filter can replace this tool without changing the chezmoi external structure.

## Development

Tested through the uv workspace; the deployed artifact is just this file tree, nothing is installed.

```sh
uv run pytest src/python/skill_filter
uv run ruff check src/python/skill_filter
```

## Performance

`chezmoi apply` runs this filter command once per external — 309 times as of this writing — so per-spawn cost dominates, and the two things that matter are which interpreter runs it and what it imports.

Always invoke the script with the Python `-S` flag, which bypasses `site` module initialization and its scan for site-packages.
The saving depends entirely on how much is installed in the interpreter being used: on a uv-managed interpreter with a near-empty site-packages it is only ~2ms per spawn (26.3ms against 28.5ms, measured over 60 spawns), while an interpreter with a large site-packages loses far more.
Treat `-S` as cheap insurance against the bad case rather than a guaranteed win, and never remove it on the evidence of one machine.

Startup and imports, not the work itself, are most of a run.
Measured on a uv-managed 3.14, per spawn: bare interpreter 11.8ms, `os`/`sys`/`hashlib` 13.8ms, and all nine module-level imports 22.7ms, against ~38ms for a full cache-hit run.
Precompiling to `.pyc` was measured and does not help — compiling this file is ~1ms, below the run-to-run noise.
The unexploited saving is that a cache hit needs neither `tarfile` nor `gzip`.
