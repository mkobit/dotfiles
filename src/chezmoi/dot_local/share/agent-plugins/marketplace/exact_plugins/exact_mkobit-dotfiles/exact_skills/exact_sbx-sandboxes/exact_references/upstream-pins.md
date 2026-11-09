# Upstream pins

The AGY environment references [`docker/sbx-kits-contrib`](https://github.com/docker/sbx-kits-contrib) at commit `21e1928b5fe0036163307ea8047e48390f2d6fec` under directory `antigravity`.

The codeload archive for that commit has SHA-256 `6fba87a5f2e3b76003e9efe3410572cbb47d925adc8b1aaafeab2f786841b0e9`.

Review the kit and update both values together before changing the environment template.

The upstream kit installs and self-updates AGY, so the kit source is pinned but the installed AGY binary remains rolling.

SBX Git kit references use `#ref=<commit>` to select an immutable revision.
