# CI response contract

Task 7 must bind CI results to the exact tested and reviewed commit.
Read-only probes used [PR 1014](https://github.com/mkobit/dotfiles/pull/1014) at `b1d16d0dad40af7209ff44d261fe14bd4cb2a66a`.
[Run 41757392141](https://github.com/mkobit/dotfiles/actions/runs/41757392141) had seven registered required checks: four passed and three integration checks were in progress.
This observation does not establish completion for a later head.

## Native response shapes

Use `gh api --paginate --slurp` and API version `2022-11-28`.
The installed CLI rejects `--slurp` with `--jq` or `--template`; parse complete JSON in Python.
Supply the full expected SHA in each endpoint and use argument lists.

| Endpoint | Slurped response |
| --- | --- |
| `repos/OWNER/REPO/commits/SHA/check-runs?per_page=100&filter=all` | Array of page objects with `total_count` and `check_runs` |
| `repos/OWNER/REPO/commits/SHA/statuses?per_page=100` | Array of page arrays |
| `repos/OWNER/REPO/commits/SHA/status?per_page=100` | Array of page objects with `sha`, `state`, `total_count`, and `statuses` |

The combined status does not include check runs.
The observed status list was empty while all seven check runs existed.
A `per_page=2` probe returned four check-run pages with sizes `[2, 2, 2, 1]` and seven unique IDs.
Flatten and validate all pages before matching names.

## Required gate

Validate PR repository, branches, and head before querying results.
Require each check run's `head_sha` to match the expected commit.
Keep its ID, exact name, app ID, suite ID, status, conclusion, and evidence URL.
Pass only `status == completed` with `conclusion == success` for every frozen required name.

Wait within a monotonic deadline for registration, missing names, queued checks, and in-progress checks.
Empty results, skipped, cancelled, neutral, failed, unknown, malformed, or denied results cannot pass.
Reject ambiguous duplicate required names, including names present in both status and check-run results.
Do not select a convenient old success or infer attempt order from array order or check-run ID.
Re-read the PR and results before merge; require the local, tested, reviewed, and live head to match.
Supply `--match-head-commit SHA`.

The observed required set uses check runs only.
Nonempty status selection and automatic rerun reduction remain unproved; do not silently enable them.
Actions run and job responses expose `run_attempt`; check runs do not expose that numeric field.
`job.check_run_url` supplies the explicit check-run join.
Only attempt 1 was observed; no rerun was requested.

## Evidence

Primary responses: [SHA-scoped check runs](https://api.github.com/repos/mkobit/dotfiles/commits/b1d16d0dad40af7209ff44d261fe14bd4cb2a66a/check-runs?per_page=100&filter=all) and [commit statuses](https://api.github.com/repos/mkobit/dotfiles/commits/b1d16d0dad40af7209ff44d261fe14bd4cb2a66a/statuses?per_page=100).
The full local report is `/tmp/sbx-rearch-ci-shape-contract.md`.
No GitHub write, tracker operation, SBX operation, or live setting change was performed.
