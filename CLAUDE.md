# Preferences

- Always write titles in sentence case.
- Write documentation (README, HTML, Markdown, AsciiDoc, RST, and other formats) with one sentence per line.
- Prefer `fd` over `find`.
- Prefer `rg` over `grep`.
- Prefer available agentic file searching and read tools over CLI tools when available.
- Prefer strict TypeScript configuration.

## Troubleshooting Package Installations
When resolving package installation failures (e.g. `npm`, `pnpm`, `bun`, `uv`), check if the failure is due to the minimum release age configuration (e.g. `min-release-age`, `minimumReleaseAge`, `exclude-newer`). If so, the package might be too new and you should use an older version.
