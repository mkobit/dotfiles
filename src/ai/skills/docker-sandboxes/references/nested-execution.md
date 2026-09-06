# Nested execution

## Coordinator and sandbox roles

The host agent acts as the root coordinator holding host credentials (SSH keys, forge tokens, database remotes) to manage branching, quality gates, and PR delivery.
The host coordinator treats the sandbox as an agentically executed environment.
It dispatches build, test, and subagent workloads into an isolated Docker Sandbox microVM via `sbx env exec` or `sbx exec`.
Host secrets and credentials never enter the microVM container.

## End-to-end delegation lifecycle

Delegate tasks to run end-to-end inside the sandbox microVM.
Consider using a subagent to probe and monitor execution as the sandbox runs.
When the sandbox workload exits, inspect and verify the work on the host (directly or with an evaluator subagent) to confirm goals are met prior to any commit or push.

## Workspace state flow

Workspace state flows directly through bind mounts or the sandbox Git daemon remote (`sandbox-<name>` under `clone: true`).
This allows the host agent to inspect, test, and publish changes without exposing host secrets inside the container.
Autonomous subagent tasks use `clone: true` so the agent works in an isolated in-VM clone until changes are fetched and reviewed on the host.

## Toolchain updates

Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`.
Alternatively, resolve toolchain updates by tearing down the environment with `sbx env rm` for a clean kit rebuild.
