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

## Binary tool upgrade PRs

The [binary upgrade workflow](binary-tool-updates.yml) includes the old and new versions in each PR title.
The description contains release notes for releases between those versions, with upstream release and comparison links.
A later run updates the PR title and description even when the remote catalog content is unchanged.
If the full release notes exceed GitHub's PR body limit, the updater selects an earlier mature release whose complete notes fit.
If no newer mature target fits, it reports an error and leaves the catalog unchanged.

The generation job reads release metadata with the read-only workflow token.
It passes only catalog and report data to a fresh publication runner.
The publication job obtains `BIN_UPDATER_TOKEN` from the `binary-updater` environment.
It opens or refreshes PRs. Required builds start automatically and merge is manual.

### Claude native updates

Claude keeps its native vendor download URLs.
The updater uses [official GitHub releases](https://github.com/anthropics/claude-code/releases) for release dates and notes, with a seven-day minimum age.
It reads all configured platform checksums from the selected version's vendor manifest before it writes the catalog.
The manifest must match the selected version, contain each configured platform, name the `claude` binary, and provide valid SHA256 checksums.
Vendor manifest requests do not receive GitHub credentials.
This validates checksum metadata over HTTPS; it does not verify the manifest's GPG signature.
See [Claude binary integrity](https://code.claude.com/docs/en/setup#binary-integrity-and-code-signing).

### Move the publication token

1. Disable the legacy `upgrade-bin-tools.yml` workflow **before merging** this replacement.
   Do not re-enable the old workflow. A rerun can use the original workflow revision and its fallback credentials.
   Check queued and active runs that could have received the repository secret.
   Cancel or drain those runs and verify their termination. Revoke the old PAT and use a scoped replacement if you cannot verify termination.
2. Find open updater PRs and disable any pending automatic merge. Verify that no pending requests remain.
3. Create the `binary-updater` environment. Allow only the `main` branch under **Selected branches and tags**. Add no tag rule or required reviewers.
   Verify the branch rule independently of the workflow guard. Use a harmless job with the environment reference and no secret reference.
4. Add `BIN_UPDATER_TOKEN` as an environment secret. Limit the token to this repository and give it only **Contents** and **Pull requests** write access.
   Set an expiry and track renewal. Remove the repository copy and confirm that no same-name inherited secret is available.
5. Merge the replacement after checking that CI jobs that execute proposed binaries lack write permissions and protected secrets.
   Run **Update binary tools** from `main` with one tool that has an eligible update.
   Confirm the catalog changes, PR title and notes, automatic checks, and manual merge.
   Confirm the retired workflow cannot run again.

Keep publication paused if validation fails. Correct the environment or workflow before resuming.
If you suspect token disclosure, revoke the token, review related branches and PRs, and install a scoped replacement in the environment.
The branch policy trusts actors who can merge changes to `main`.
See [environment controls](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) and [workflow reruns](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs).
