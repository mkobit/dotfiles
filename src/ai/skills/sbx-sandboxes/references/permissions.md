# Permissions

Task authorization defines the permitted work.
Platform approval defines whether a command can run outside the current sandbox.
A runtime failure does not grant new authority.

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

Lifecycle changes, credential changes, diagnostic upload, sandbox removal, and publication require their own task authority and platform approval.
A command grant does not authorize those actions.
Help with `--help` displays usage; it does not grant execution of the underlying operation.

## Host support

Claude Code supports skill tool grants during the invoking turn, subject to managed restrictions.
See [Claude Code skill permissions](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill).

Codex has no supported plugin command-grant mechanism in the installed version.
A trusted repository can provide persistent `.codex/rules/*.rules` after authorization.
Codex rules match argument prefixes, not Bash glob patterns:

```starlark
prefix_rule(pattern = ["sbx", "env", "exec", ".sbx/sbxenv.yaml", "--"], decision = "allow")
prefix_rule(pattern = ["sbx", "exec", "project-codex"], decision = "allow")
```

These examples cover guest writes and do not expire with the skill turn.
See [Codex rules](https://developers.openai.com/codex/rules).

The shared global command catalog supplies narrow help, listing, and version grants to supported permission renderers.
Its command heads are literal; do not put globs into that catalog.
AGY and other hosts must use their supported approval mechanisms where skill metadata is not enforced.
Cross-tool conversion is outside this skill.

## Failures and results

For socket, network, or state access failures, follow the active tool's escalation policy and retry before diagnosing authentication.
A login service error can come from restricted access.
Once host-service restrictions are confirmed, use the required platform access for later `sbx` commands; the CLI is a host client, and workloads still run in SBX.
Use [Authentication](authentication.md) to distinguish these failures from expired sessions and sign-in failures.
Request only the reusable command head needed by the task; never the whole `sbx` prefix.
Preserve each failed exit code and report which checks ran in SBX, on the host, or remain blocked.
