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
Combine `clone: false` with dedicated Git worktrees to distribute work across parallel sandboxes without file collisions.

Set `clone: true` only for a private clone with an explicit host return process.

Do not track host credentials, additional writable host paths, or host command bridges in repository environments.

Keep host secrets, bindings, registries, and local-command MCP servers outside the sandbox environment.

Run `sbx env plan .sbx/sbxenv.yaml` before creation.

After changing kit, workspace, ports, or environment variables, use the [lifecycle plan](repository-setup.md#lifecycle).
Preserve incomplete work and follow the [recovery ownership gate](../../sbx-orchestrator/references/recovery.md#resume-or-replace-a-worker) before any replacement writer.
Rebuild or removal needs the applicable authority and preserved evidence.

## Ports

Declare only sandbox ports in environment manifests.
Omit `host` so SBX allocates host ports dynamically.
Static host ports cause allocation conflicts when sandboxes or host processes use the same port.

```yaml
ports:
  - sandbox: 6080
  - sandbox: 5900
  - sandbox: 9222
  - sandbox: 5173
```

Use `sbx ports <sandbox>` to inspect allocated host ports.
