# Permissions

Task authorization controls whether a change or environment action is in scope.

Platform approval controls whether a command can run outside the current sandbox.

A runtime failure is evidence to inspect, not a new grant of task authority.

## Claude Code

The skill frontmatter grants these command patterns during the turn that invokes it:

- `sbx ls --format json` inspects existing environments.
- `sbx kit validate .sbx/kit` validates the conventional kit.
- `sbx env plan .sbx/sbxenv.yaml` plans the conventional environment.
- `sbx env exec .sbx/sbxenv.yaml -- *` runs a command in that environment.

The `allowed-tools` grant clears on the next user message and cannot override managed permission restrictions.

The path in the exec grant identifies a reviewed configuration file, but it does not freeze that file's contents.

With `workspace.clone: false`, commands run through `sbx env exec` can write to the host checkout through the direct mount.

Other SBX commands and alternate environment paths follow the normal approval flow.

See [Claude Code skill permissions](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill).

## Codex

The installed Codex version has no supported plugin command-grant mechanism.

A consuming repository can copy the reviewed example to `.codex/rules/sbx.rules` in a trusted project.

The rules filename must end in `.rules`.

Codex loads project rules at startup after the project configuration layer is trusted.

These persistent rules are not supplied by this skill and do not end with the skill turn.

For the conventional repository paths, a repository may choose this example after approval:

```starlark
prefix_rule(pattern = ["sbx", "kit", "validate", ".sbx/kit"], decision = "allow")
prefix_rule(pattern = ["sbx", "env", "plan", ".sbx/sbxenv.yaml"], decision = "allow")
prefix_rule(pattern = ["sbx", "env", "exec", ".sbx/sbxenv.yaml", "--"], decision = "allow")
prefix_rule(pattern = ["sbx", "ls", "--format", "json"], decision = "allow")
```

The exec rule matches later arguments after `--`, so it can run commands that write through a direct mount.

Review the environment configuration and obtain the applicable user authorization before saving persistent rules.

See [Codex project rules](https://learn.chatgpt.com/docs/agent-configuration/rules).

## Escalation and results

After a restricted socket or Docker login error, follow the active tool's escalation policy and retry the affected command when that policy requires it.

Inspect the retry result before diagnosis, because a login error may have another cause.

When a reusable prefix is appropriate, request only the command head needed for the task, never the whole `sbx` prefix.

Group related delegated checks when practical, but preserve each failed exit code.

Report which checks ran in SBX, which ran on the host, and which remain blocked.

Repository and session instructions govern host checks.
