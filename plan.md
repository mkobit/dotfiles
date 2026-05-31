1. Update `claude_code` version to `2.1.150` in `src/chezmoi/.chezmoidata/claude_code.toml`
   - It is > 7 days old, according to npm info.
2. Update `mise` to `v2026.5.14` in `src/chezmoi/.chezmoidata/bin/mise.toml`
   - It is 8 days old (latest stable > 7 days).
3. Update `fzf` to `0.73.0` in `src/chezmoi/.chezmoidata/bin/fzf.toml`
   - It is 7 days old.
4. Update `chafa` to `1.18.2` in `src/chezmoi/.chezmoidata/bin/chafa.toml`
   - It is 31 days old.
5. Update `gh` to `2.93.0` in `src/chezmoi/.chezmoidata/bin/gh.toml`
   - It is 17 days old.
6. Update python and other managed versions in `src/chezmoi/.chezmoidata/bin/mise.toml`
   - Update python to `3.14.5`
   - Update pnpm, node, etc. to their latest versions that are older than 7 days using manual bump. (Wait, let's bump `pnpm` and `node` to what we found: `node` -> `22.14.0` is already there. Wait, `mise outdated` did not work. I will run `npm info node time` to find latest version and bump. Oh node is not an npm package. Let's just bump the ones I clearly found updates for: `python` to `3.14.5`). Wait! I will leave `python@3.14.4` alone if I can't be sure 3.14.5 is > 7 days. Oh, wait, 3.14.5 is just a patch, usually safe, but let's check.
7. Run tests to ensure syntactically valid TOML files using `tomllib`.
8. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
9. Submit the branch.
