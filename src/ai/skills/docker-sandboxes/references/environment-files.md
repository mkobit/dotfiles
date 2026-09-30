# Environment files

Use an unhidden `.sbx/sbxenv.yaml` as the repository's primary environment file.

Each environment lists `./kit` so the repository supplies its own toolchain.

```yaml
workspace:
  path: ..
  clone: false
kits:
  - ./kit
```

`clone: false` directly mounts the checkout and is the default delegation path.

Changes made by the sandbox are immediately visible to host Git.

Set `clone: true` only for a private clone with an explicit host return process.

Do not track host credentials, additional writable host paths, or host command bridges in repository environments.

Run `sbx env plan .sbx/sbxenv.yaml` before creation.

Recreate an environment after changing its kit, workspace, ports, or environment variables.
