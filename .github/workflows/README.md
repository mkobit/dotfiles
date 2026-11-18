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

The [binary upgrade workflow](upgrade-bin-tools.yml) includes the old and new versions in each PR title.
The description contains release notes for releases between those versions, with upstream release and comparison links.
A later run updates the PR title and description even when the remote catalog content is unchanged.
If the full release notes exceed GitHub's PR body limit, the updater selects an earlier mature release whose complete notes fit.
If no newer mature target fits, it reports an error and leaves the catalog unchanged.

The workflow uses a GitHub App installation token when `BIN_UPDATER_APP_CLIENT_ID` is set.
It restricts that token to this repository with contents and pull requests write permissions.
The token is used for Git pushes and PR operations.
Upstream release lookup uses the read access available through `GITHUB_TOKEN`.

### Claude native updates

Claude keeps its native vendor download URLs.
The updater uses [official GitHub releases](https://github.com/anthropics/claude-code/releases) for release dates and notes, with a seven-day minimum age.
It reads all configured platform checksums from the selected version's vendor manifest before it writes the catalog.
The manifest must match the selected version, contain each configured platform, name the `claude` binary, and provide valid SHA256 checksums.
Vendor manifest requests do not receive GitHub credentials.
This validates checksum metadata over HTTPS; it does not verify the manifest's GPG signature.
See [Claude binary integrity](https://code.claude.com/docs/en/setup#binary-integrity-and-code-signing).

### Set up the GitHub App

1. Open your GitHub account settings, then **Developer settings**, **GitHub Apps**, and **New GitHub App**.
   Give the App a name and use this repository URL as its homepage.
   Clear **Active** under webhook settings; this App does not receive events.
2. Set repository permissions **Contents** and **Pull requests** to **Read and write**.
   Leave other permissions unchanged.
   Limit installation to your account when you register the App.
3. Install the App on `mkobit/dotfiles` only.
4. Generate a private key from the App settings and save the PEM file in a secure local path.
5. Under this repository's **Settings**, **Secrets and variables**, **Actions**, add the variable `BIN_UPDATER_APP_CLIENT_ID` with the App's client ID.
   Add the secret `BIN_UPDATER_APP_PRIVATE_KEY` with the complete PEM file content.
   Keep the private key outside Git and chat.
6. After this workflow change is merged, run **Upgrade binary tools** with one tool that has an eligible update.
   Confirm that the PR title contains both versions, the body contains the intervening release notes, and required PR workflows start without approval.

These settings can also be stored with the GitHub CLI:

```sh
gh variable set BIN_UPDATER_APP_CLIENT_ID --repo mkobit/dotfiles --body 'REPLACE_WITH_CLIENT_ID'
gh secret set BIN_UPDATER_APP_PRIVATE_KEY --repo mkobit/dotfiles < /secure/path/binary-updater.pem
```

If the App client ID is absent, the workflow uses the existing `BIN_UPDATER_TOKEN` secret, then `GITHUB_TOKEN`.
The `GITHUB_TOKEN` fallback requires approval for PR builds.
An App configuration error fails the token step; it does not silently fall back.
App tokens expire after one hour and the token action revokes its token at job completion.

See [GitHub App registration](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app), [installation token creation](https://github.com/actions/create-github-app-token/tree/v3.3.0), and [workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
