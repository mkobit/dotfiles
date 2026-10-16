# Nested execution

The host coordinator owns task selection, branch state, review, Git commits, signing, and pushes.

The sandbox implements the delegated task, including file edits, builds, tests, and generators.

Host credentials stay on the host.

## Delegation lifecycle

1. Claim a bead on the host that can finish in one repository.
2. Supply the bead context, file ownership, acceptance criteria, required checks, and log location.
3. Dispatch immediately to an existing environment with unchanged configuration.
4. Review the diff, command exit status, and check results on the host.
5. Update the bead on the host and report the result and log location.

Delegation authorizes implementation and checks within the assigned scope.
Do not substitute read-only research or request routine approval to edit files.
Choose a bounded task over broad design or cross-repository work, even when the broader task has higher priority.
Keep Beads writes, credentials, commits, signing, and publication on the host.

Save detailed output in task logs and return a short result.
Run the required checks once and repeat only after relevant changes or failures.
For a missing environment or changed configuration, use [Repository setup](repository-setup.md).
For execution errors, use [CLI automation](cli-automation.md).

The standard `clone: false` workspace returns file edits immediately to the host checkout.

Use a private clone only when isolation outweighs that fast review loop and the repository specifies the return path.
