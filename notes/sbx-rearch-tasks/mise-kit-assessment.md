# Mise kit assessment

Assessment date: 2026-11-02.
Scope: read-only review of the published kit and its use with the repository environment.
No repository files or sandbox environments changed.

## Recommendation

Keep the current kit for this change.
The root agent reports that the current configuration passed fresh native creation and 22 tests.
The Docker kit is a suitable follow-up candidate to replace the npm bootstrap, but it changes mise from `2026.10.23` to `2026.5.2`.
Check the repository lockfile and tool installation with that older release before adoption.
Separate kit repositories and use in other repositories remain follow-ups.

## Published artifact

Docker Hub identifies Docker, Inc as the verified publisher.
The page links the `mise` directory in `docker/sbx-kits-contrib` as its source.
The selected artifact digest is `sha256:21efbf187ee9950b0b3a3bba6d68939bbebe68f853567618536dd9b18a947a59`.
The `latest` tag can change; use the digest in tracked configuration.
See the [Docker Hub listing](https://hub.docker.com/r/sbx/mise-kit) and [source repository](https://github.com/docker/sbx-kits-contrib/tree/main/mise).

Native inspection passed with this exact reference:

```sh
sbx kit inspect docker.io/sbx/mise-kit@sha256:21efbf187ee9950b0b3a3bba6d68939bbebe68f853567618536dd9b18a947a59 --format json
```

The result has `schemaVersion: "2"`, `kind: mixin`, and `name: mise`.
It has no kit `version` field and no input arguments.
It installs mise `2026.5.2` in `/usr/local/bin/mise` as root.
The installer downloads a fixed GitHub release and checks an architecture-specific SHA-256 before extraction.
It supports Linux `amd64` and `arm64`.
The SHA-256 values are `cdf616b3d8554bece574cb1a5c0f19cc0f551dffbecf66037df1cc06569a42ef` and `a746ad85fe8a7b62a6c72939da5fb4231074fd16c482f6334a598bd92926f41e`, respectively.
These values match the inspected artifact and [upstream specification](https://github.com/docker/sbx-kits-contrib/blob/main/mise/spec.yaml).

`sbx kit provenance` found signed provenance but required a signer identity before it would verify or print it.
Signer verification and the source commit were not established in this assessment.

## Supported composition

The following replacement for the existing `kits` list uses the supported environment-file syntax:

```yaml
kits:
  - docker.io/sbx/mise-kit@sha256:21efbf187ee9950b0b3a3bba6d68939bbebe68f853567618536dd9b18a947a59
  - ./kit
```

Keep `agent: codex`, the pinned `sandboxOptions.template`, and the workspace settings.
The mise mixin does not select an agent or replace the base image.
Install commands run in kit order, so mise is installed before the repository kit uses it.
Network lists combine and environment variables use the last value for each key.
Use the environment `kits` list; author-time `mixins` in a kit specification is not implemented in the reviewed v2 runtime contract.
See [environment-file kits](https://docs.docker.com/ai/sandboxes/configuration/environment-files/#kits) and [v2 composition rules](https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md#7-composition--distribution).

Native artifact loading passed.
This composition was not used to create a sandbox in this assessment.

## Repository changes needed for adoption

The repository installer would remove the npm mise installation, its bootstrap PATH entry, and its mise symlink.
The existing PATH already contains `/usr/local/bin`.
The repository would retain the exact uv, Python, and chezmoi versions, their tool symlinks, and its runtime checks.
The npm registry permission can be removed if no remaining install requires it.

The upstream kit adds Bash activation and sets `MISE_TRUSTED_CONFIG_PATHS=/`.
It adds GitHub network access, but no language runtimes or repository tool versions.
The whole-filesystem trust setting changes the current explicit `mise trust mise.toml` behavior.
Review that change before adoption.
Non-interactive commands should continue to use `mise exec` or explicit executable paths.
See the [kit behavior](https://github.com/docker/sbx-kits-contrib/blob/main/mise/README.md).

## Release age and reproducibility

Keep `MISE_MINIMUM_RELEASE_AGE: "7d"` and `UV_EXCLUDE_NEWER: P7D` in the repository kit.
The upstream kit does not set either value.
Mise `2026.5.2` supports the release-age setting.
Its filter applies to version selection where the backend supplies dates; exact pins usually bypass it, and versions without dates pass.
Its `locked` setting requires resolved lockfile URLs and is compatible with enabled lockfile support.
See the [settings source for mise 2026.5.2](https://github.com/jdx/mise/blob/v2026.5.2/settings.toml#L1107) and the [release-age definition](https://github.com/jdx/mise/blob/v2026.5.2/settings.toml#L1224).

The OCI digest fixes the kit content.
The embedded SHA-256 values fix the mise archive content.
The pinned base image fixes its image content.
These controls do not make all later runtime downloads reproducible.
Tool URLs, checksums, backend selection, Python build selection, locked dependencies, and agent startup downloads also need fixed inputs.
A seven-day age limit restricts eligible releases; it does not lock them.
Fresh creation remains the required test after adoption.
