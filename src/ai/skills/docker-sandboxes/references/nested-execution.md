# Nested execution

## Coordinator and sandbox roles

The host agent acts as the root coordinator holding host credentials (SSH keys, forge tokens, database remotes) to manage branching, quality gates, and PR delivery.
The host coordinator treats the sandbox as an agentically executed environment.
It dispatches build, test, and subagent workloads into an isolated Docker Sandbox microVM via `sbx env exec` or `sbx exec`.
Host secrets and credentials never enter the microVM container.

## Workspace state flow

Workspace state flows directly through bind mounts or the sandbox Git daemon remote (`sandbox-<name>` under `clone: true`).
This allows the host agent to inspect, test, and publish changes without exposing host secrets inside the container.
Autonomous subagent tasks use `clone: true` so the agent works in an isolated in-VM clone until changes are fetched and reviewed on the host.

## Toolchain updates

Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`.
Alternatively, resolve toolchain updates by tearing down the environment with `sbx env rm` for a clean kit rebuild.
