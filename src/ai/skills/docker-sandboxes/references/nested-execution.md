# Nested execution

## Coordinator and sandbox roles

The host agent acts as the root coordinator holding host credentials (SSH keys, forge tokens, database remotes) to manage branching, quality gates, and PR delivery.
The host coordinator treats the sandbox as an isolated execution environment.
It dispatches build, test, and subagent workloads into an isolated Docker Sandbox microVM via `sbx env exec` or `sbx env run`.
Host secrets, credentials, and host checkouts never enter the microVM container.

## End-to-end delegation lifecycle

1. Verify environment health and plan:
   `sbx kit validate .sbx/kit`
   `sbx env plan .sbx/sbxenv.yaml`
2. Provision or ensure sandbox container is running:
   `sbx env create .sbx/sbxenv.yaml`
3. Dispatch verification or build tasks:
   `sbx env exec .sbx/sbxenv.yaml -- mise run check`
4. Inspect command outputs, exit codes, and test artifacts.
5. If running an autonomous inner agent session, launch with `sbx env run .sbx/sbxenv.yaml`.
6. When the inner task completes, inspect and retrieve changes on the host.
7. Teardown or reset when finished:
   `sbx env rm .sbx/sbxenv.yaml --force`

## Workspace state flow and retrieval

Autonomous subagent tasks use `clone: true` so the agent works in an isolated in-VM clone at `/workspace`.
When changes are made and committed inside the sandbox, they remain inside the microVM's internal repository.
The microVM exposes a local git daemon remote named `sandbox-<name>` on the host.
To pull changes back to the host checkout:
1. Fetch the committed branch from the sandbox remote:
   `git fetch sandbox-<name> <branch>`
2. Inspect the fetched commit log and diff on the host:
   `git log -p FETCH_HEAD`
3. Merge or cherry-pick into the host working branch:
   `git merge --ff-only FETCH_HEAD` (or `git cherry-pick FETCH_HEAD`)
4. Run host-side verification gates and sign commits with host signing credentials.

## In-place toolchain and package updates

Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`.
Alternatively, resolve toolchain updates cleanly by tearing down the environment with `sbx env rm .sbx/sbxenv.yaml --force` and recreating it to trigger kit rebuild.

