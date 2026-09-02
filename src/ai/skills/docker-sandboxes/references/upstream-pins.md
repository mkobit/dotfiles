# Upstream pins

The AGY environment references [`shelajev/agy-sbx-kit`](https://github.com/shelajev/agy-sbx-kit) at commit `3e7016f108f3cf09922cf351b55a49e38d97f9f2`.

The codeload archive for that commit has SHA-256 `cd2fec52b532a9136550ba0051bde6eb5ea17cb8f86ad9c0cb1475c54dc17d1a`.

Review the kit and update both values together before changing the environment template.

The upstream kit installs and self-updates AGY, so the kit source is pinned but the installed AGY binary remains rolling.

SBX Git kit references use `#ref=<commit>` to select an immutable revision.
