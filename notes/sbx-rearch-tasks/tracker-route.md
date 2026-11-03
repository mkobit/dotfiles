# Beads route for SBX workers

## Decision

Use the host coordinator as the only tracker writer for task 7.
The host claims the task, supplies a complete issue snapshot, and closes the issue after it independently confirms the GitHub merge.
Use this contract for direct mounts and private clones.
Do not require guest Beads access for this route.
Do not copy a database, initialize a guest tracker, mount extra tracker metadata, or give the guest tracker credentials.

This is a proposed implementation contract, not an integration test result.
No server, sandbox, policy, credential, database, or repository file was changed during this review.

## Verified facts

- Installed SBX is `v0.50.1`.
- Installed Beads binaries include `1.3.1` and `1.3.2`.
- The default `bd` shim fails because no version is selected in this execution context.
- `bd context --json` in this worktree reports that no `.beads` directory exists.
  The root coordinator must supply the actual tracker directory before a real launch.
  The host proxy described in the task was not available for a connection test here.
- In both installed versions, `bd init --proxied-server` uses a loopback proxy.
  `--proxied-server-port N` selects a fixed port; the default is dynamic.
  The managed backend configuration rejects non-loopback listeners.
  External-host flags select the proxy's backend; they do not expose its listener to the guest.
- `bd ready --claim --json` atomically selects and claims ready work.
  `bd update ID --claim --json` assigns the actor and sets `in_progress`.
  The latter accepts a repeated claim from the same actor, so actor reuse cannot exclude a duplicate worker.
  These facts come from installed help.
- `bd context --json` reads configuration without opening the database.
  It is an identity check, not a connectivity check.
- Standard server mode supports `BEADS_DOLT_SERVER_HOST`, `BEADS_DOLT_SERVER_PORT`, `BEADS_DOLT_SERVER_USER`, and `BEADS_DOLT_SERVER_TLS`.
  It also supports a password or a credentials file.
  These controls do not establish network routing or prove that proxied mode uses them.
  See the [Beads server configuration](https://github.com/gastownhall/beads/blob/v1.3.2/docs/architecture/dolt.md#server-mode-multi-writer--orchestrator).
- Docker documents a host route: guest `host.docker.internal` reaches host `localhost` through the SBX proxy when the corresponding `localhost:PORT` rule permits it.
  Guest `127.0.0.1` is not the host address.
  See [access to host services](https://docs.docker.com/ai/sandboxes/workflows/development/).
- A network permission is separate from a kit's environment variables.
  Organization policy can prevent a local allow rule from taking effect.
  See [network access policies](https://docs.docker.com/ai/sandboxes/governance/access-controls/network/).

## Host claim and snapshot sequence

Resolve a host `tracker_directory` with the existing authoritative tracker.
Save the resolved `bd` executable/version, tracker context, unique actor, and route `host-coordinator` in the launch record.
Keep these values in host state; the guest only needs the issue snapshot and run identity.
Do not accept a tracker directory from guest output at close time.

Before a claim:

1. Acquire exclusive workspace ownership and create the durable pending launch record.
2. Check the repository, environment, tools, verification command, Git credentials, signing route, and guest Git support required by the selected delivery mode.
3. Run the host context and readiness checks below.
4. For explicit selection, require the requested ID in the complete ready result and inspect its full details.
5. Record the exact initial commit and branch.

Supported commands, shown with values supplied by the host coordinator:

```text
bd -C TRACKER_DIRECTORY context --json
bd -C TRACKER_DIRECTORY ready --json --limit 0
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

The readiness command is a real database query and can start the configured managed backend.
Do not describe it as a server-free operation.

Claim with exactly one of these commands:

```text
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR ready --claim --json
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR update BEAD_ID --claim --json
```

The implementation can use `BEADS_ACTOR` instead of `--actor`; both are supported.
Use a new actor per launch record, not per retry.
After a successful claim, persist the response before branch creation or worker launch.
Read the full issue again with `bd show` and save it in the prompt and host record.
The snapshot must include the description, acceptance criteria, dependencies, owned paths, and current assignee/status.
Freeze the assignment snapshot in host-owned state and record a hash of its material requirements.
Pass the same snapshot and actor to the guest.
Do not accept guest changes to this snapshot as new task authority.
Do not import the snapshot into a guest database.

The installed help does not prove that an explicit `update --claim` also checks dependency readiness atomically.
Keep the explicit readiness check required by the draft.
Do not claim a stronger guarantee without a dedicated test or source check.

## Branch and workspace rules

Accept a clean main/default checkout for launch only when the coordinator holds exclusive workspace ownership.
After the host claim succeeds, create the assigned branch with an argument-list invocation of:

```text
git -C WORKSPACE switch -c feat/BEAD_ID EXPECTED_BASE_SHA
```

Validate the bead ID as part of a Git branch name before the claim.
Reject an existing conflicting branch before the claim.
Record and verify the new branch and unchanged base SHA before the writer starts.
A branch-creation failure after claim leaves the claim and recovery record intact.

For a private clone, verify the guest base commit and create the assigned feature branch in the exclusive guest checkout after the host claim.
The host checkout need not change branches in clone mode.
Preserve the installed clone return contract and validate `sandbox-NAME` when accepting returned commits.

`pr:ship` must always reject main/default branches and detached HEAD.
The allowance for main applies only to launch before feature-branch creation.

Keep the current linked-worktree migration edit-only.
If the guest cannot reach the `.git` target, it must not branch, commit, push, or run the guest shipping path.
The root keeps the tracker claim and performs final delivery on the host.
Do not add metadata mounts to change this mode.

## Merge confirmation and close

The guest may run all authorized PR steps through confirmed merge, then return the PR URL, repository, branch, head SHA, and checks evidence.
Its result is `merge-confirmed-close-pending`, not completed work.
This is a proposed state name, not an existing Beads status.

The host coordinator then independently runs:

```text
gh pr view PR --repo OWNER/REPOSITORY --json state,headRefOid,headRefName,baseRefName,url
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

Require `MERGED`, the expected PR head SHA, repository, head branch, and base branch.
Require that the tracker still identifies the claimed issue and expected owner.
Compare the current description, design, acceptance criteria, dependencies, and agreed scope with the frozen assignment snapshot.
If these requirements changed, preserve the open issue and report the difference for host review, even when the PR merged.
Exclude routine audit timestamps and the expected status transition from this comparison.
Then close through the saved host route:

```text
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR close BEAD_ID --reason REASON --json
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

The reason must include the verified PR URL and head SHA.
Require the final issue status to be closed before the overall launch is complete.
Do not infer merge from a zero harness status or a zero `gh pr merge` status.
If merge is queued, leave the claim open.
If close fails after a confirmed merge, retain `merge-confirmed-close-pending` and retry only confirmation/close through the saved route.
Do not repeat implementation, create another PR, or launch another worker.
If the coordinator stops, recovery must use the same record and actor after it proves that the previous worker has stopped.

For guest `pr:ship`, pass the host-close mode through a controlled launch contract.
Do not make every missing guest tracker silently mean success.
A standalone `pr:ship` without a tracker or a host coordinator contract must fail before publication.

## Failure handling

| Failure point | Required result |
| --- | --- |
| Missing tools, tracker, route, environment, or exclusive workspace before claim | Stop with no claim and no worker |
| No ready issue | Exit zero with a plain message and no worker |
| Claim refused | Stop with no worker |
| Claim command times out or disconnects | Mark claim outcome unknown; query the same tracker and actor before recovery |
| Snapshot, branch creation, or launch fails after claim | Keep the claim, workspace lock record, and evidence |
| Worker disconnects | Preserve pending state; do not launch a replacement until ownership is resolved |
| Merge is queued or unconfirmed | Keep the claim open |
| Merge confirmed but host close fails | Preserve the pending-close state and retry close |

Never auto-unclaim a task after a launch error.
A failure response can follow a successful claim when the connection is lost.

## Shared service alternative

A shared route is feasible, but it needs more setup and validation than the host-owned route.
Do not add it implicitly to task 7.

Installed `bd serve` provides an HTTP API over the same tracker.
The host can bind a fixed loopback port and permit the host-service name:

```text
bd -C TRACKER_DIRECTORY serve --addr 127.0.0.1:PORT --allowed-host host.docker.internal:PORT
```

Run it under a host supervisor if this route is selected.
Validate the exact `Host` value received through SBX before finalizing `--allowed-host`.
The HTTP readiness request is `GET /v0/beads/ready?limit=1`; `/healthz` checks process liveness only.
Fetch `/v0` and `/v0/beads/context` to establish the supported claim and close operations before writing a client.
Do not assume `bd` has an HTTP endpoint environment variable; none was verified.
See the [versioned HTTP server implementation](https://github.com/gastownhall/beads/blob/v1.3.2/cmd/bd/serve.go).

For the existing v2 kit format, a fixed-port route can declare the following fragment:

```yaml
permissions:
  network:
    allow:
      - localhost:PORT
environment:
  variables:
    TRACKER_API_URL: http://host.docker.internal:PORT
```

Replace `PORT` with one configured numeric value before validation.
`TRACKER_API_URL` is a proposed application variable, not a Beads variable.
The complete kit must retain its required fields and pinned tool installation.
Use [kit network declarations](https://docs.docker.com/ai/sandboxes/customize/kits-v2/#network) and [environment files](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) for reproducible setup.
Do not use sandbox `ports` declarations to expose a host service; those publish guest services on the host.

Loopback HTTP authentication is optional in Beads.
Its use through the host proxy requires an explicit review of which sandboxes can reach the port.
If authentication is required, use an approved SBX credential injection route and validate it; do not put tokens in arguments, kit variables, snapshots, or records.
This investigation did not verify a suitable injection declaration for this API.
Do not bind non-loopback or use `--insecure-no-auth` to avoid this prerequisite.

Standard SQL server access is another supported Beads capability, but it requires an actual reachable server and connection metadata for the correct database.
The Docker host-service HTTP example does not prove that raw Dolt SQL works through this path.
No raw SQL transport test was run.
It is not achieved by copying the host proxied configuration or setting guest `BEADS_DOLT_SERVER_HOST` alone.
A fixed proxy port also requires a live host process; changing the guest hostname does not provide proxy startup after its idle timeout.

If a shared service is implemented later, its host service and SBX settings must be owned by chezmoi source and converge through plain `chezmoi apply`.
Repository kit/environment files must reproduce the guest configuration.
Other repositories and new kit repositories remain follow-up work.

## Draft changes required

The current `tasks.md` launch section conflicts with the required main-checkout behavior: it requires a clean feature branch before launch.
Replace that sentence with the exclusive-ownership, claim, then branch sequence above.
Limit the test that rejects main/default branches to shipping; add a launch test that accepts clean main.

Preflight item 5 currently requires tracker availability in the guest.
Make it route-specific: host readiness for `host-coordinator`; guest connectivity and authoritative identity for a future shared route.

The draft already permits a snapshot and one tracker owner for clones.
Extend this to direct mode and make host close an explicit required completion step.
PR delivery step 13 already names the designated owner, but guest `pr:ship` needs the pending-close return contract above.
The generic worker prompt currently requires guest `pr:ship` in all cases; preserve the edit-only migration exception.

## Required tests and prerequisites

Use command-stub tests for both direct and clone launches:

- Assert only host `bd` receives claim and close calls, always with the saved tracker directory and actor.
- Assert the guest receives a full snapshot and never runs `bd init`, `bd import`, or a claim.
- Accept clean main for launch and require claim before feature-branch creation and before writer launch.
- Reject main, detached HEAD, and dirty state in shipping.
- Reject duplicate workspace launches even when an actor is reused.
- Test empty ready work, explicit readiness rejection, claim failure, ambiguous claim outcome, and failures after claim.
- Test host-close completion after independent merge confirmation.
- Test queued merge, wrong head/repository, close failure, and recovery after a lost coordinator.
- Change material task requirements after claim and assert that host close is refused despite a confirmed merge.
- Test that missing tracker access without an explicit coordinator contract fails before publication.
- Test clone base/return validation separately from tracker ownership.
- Test that the linked-worktree migration cannot invoke guest shipping.

Before real use, resolve the actual host tracker and select the installed `bd` version reproducibly.
Prove the existing repository kit, signing route, GitHub access, verification task, and clone return path in their own integration checks.
These prerequisites were not tested by this read-only investigation.
No shared tracker service is required for the recommended route.
