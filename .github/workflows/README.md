# Workflow dependencies

Workflows use full release tags with exact action commits recorded in [actions.lock](actions.lock).
Review workflow and lock changes together.

## Updating dependencies

Install the qualified lock tool once with an authenticated GitHub CLI:

```sh
gh extension install github/gh-actions-lock --pin v0.4.0
```

From the repository root, generate the lock and verify upstream provenance:

```sh
gh actions-lock --migrate-local-actions
gh actions-lock --verify
```

Commit the generated lock and migrated references together.
Regenerating without dependency changes should produce no diff.
Remove redundant generated trailing version comments if the comment check rejects them, then verify again.
The verification workflow independently installs v0.4.0 and uses the standard workflow token with read-only repository permissions.
Its output records `github.workflow_sha` for comparison with runner action-preparation logs before merge.

Dependabot waits 21 days before proposing Actions version updates and maintains matching lock entries.
Security updates are exempt from this cooldown, and manual workflow or lock edits require review regardless of release age.
The uv cooldown remains 14 days.

## Local actions and coverage

`$/.github/actions/setup-mise` resolves from the workflow repository at the workflow commit, independently of checked-out workspace action files.
Migration allows the lock tool to follow its nested remote dependency.
The composite action retains its mise version lookup from the checked-out binary catalog.

`jdx/mise-action` retains SHA `8008c3f4db491fde6fd6d72dc97fbdb752dac949` and is included in lock coverage for both CI and binary upgrades.
No full release tag matches that commit, and switching to an eligible older release would remove an existing cache-hang fix.
Keep this exception until a suitable release satisfies the 21-day version policy.

Reusable workflows from other repositories require separate commit pins, and container images require digest pins because the lock tool does not cover them.
Downloads in shell commands and the separately version-pinned lock-tool bootstrap are outside action lock coverage.
See the [v0.4.0 limitations](https://github.com/github/gh-actions-lock/tree/v0.4.0#limitations) and the [native lockfile contract](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles).
