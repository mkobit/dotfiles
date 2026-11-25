# Permissions

Task authorization defines the permitted work.
Platform approval defines whether a command can run outside the current sandbox.
A runtime failure does not grant new authority.
Reuse approved task authority for routine edits, checks, repairs, and needed task-specific worktree or environment setup.
Do not request another confirmation solely because the task needs setup.
Ask only for missing task authority, actual platform permission, unavailable credential action, scope expansion, or a destructive unrelated change.

## Readable commands

Separate host setup and publication access from guest edit and check authority.
Guest bypass flags affect only the guest process; they grant no host access.
Show short direct commands with the selected environment, model, and thinking setting visible for coding launches.
Keep literal task data separate from command evaluation; see the [launcher](../../sbx-orchestrator/references/worker-launch.md).
Do not hide large setup or launcher programs behind helper paths or request broad command grants.
Record each extra approval cause, such as protected Git metadata, network, or process access.
Do not infer dialog counts from tool calls or promise an exact approval total.

## Standard skill grants

`allowed-tools` uses standard skill metadata with `Bash(...)` patterns.
Each agent decides whether and how it enforces that metadata.
Do not assume that Claude Code, Codex, AGY, and other hosts provide equal approval support.
See the [Agent Skills specification](https://agentskills.io/specification#allowed-tools-field).

The skill grants help, sandbox listing, version inspection, kit validation, environment planning, and diagnosis without upload.
Diagnostic formats have exact grants so `--upload` is not included.
The execution patterns cover relative paths, absolute paths, alternate filenames, multiple environment files, and guest command arguments:

```text
Bash(sbx env exec * -- *)
Bash(sbx exec *)
```

These grants permit discovery, builds, tests, coding agents, and guest writes.
With `workspace.clone: false`, guest writes change the mounted host checkout.
They also cover exec options such as user, workdir, and environment input; use only those needed by the authorized task.
Review the selected environment and task scope before execution.
A path pattern does not freeze the contents of an environment file.

Needed task-specific lifecycle setup can use the existing approved task authority.
Credential changes, diagnostic upload, unrelated removal, and publication are not implied by permission to implement a task.
A command grant does not expand task authority or bypass an actual platform restriction.
Help with `--help` displays usage; it does not grant execution of the underlying operation.

## Host support

Claude Code supports skill tool grants during the invoking turn, subject to managed restrictions.
See [Claude Code skill permissions](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill).

The plugin does not supply command approval hooks.
The skill keeps its approval list in `allowed-tools`.
Hosts that do not use this field apply their normal command approval checks.
Use the platform approval process when `sbx` needs host-service access.

The shared global command catalog grants `sbx --version` for Claude Code and AGY.
Other SBX commands use skill grants where supported or the host approval process.
Its retirement entries remove old generated grants from saved settings.
An overlay can still declare an explicit grant.

## Failures and results

For socket, network, or state access failures, follow the active tool's escalation policy and retry before diagnosing authentication.
A login service error can come from restricted access.
Once host-service restrictions are confirmed, use the required platform access for later `sbx` commands; the CLI is a host client, and workloads still run in SBX.
Use [Authentication](authentication.md) to distinguish these failures from expired sessions and sign-in failures.
Request only the reusable command head needed by the task; never the whole `sbx` prefix.
Where supported, use a narrow reusable `sbx env exec` or `sbx exec` prefix for the assigned environment.
Preserve each failed exit code and report which checks ran in SBX, on the host, or remain blocked.
