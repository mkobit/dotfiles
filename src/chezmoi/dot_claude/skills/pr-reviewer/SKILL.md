---
name: Pull request reviewer
description: Provides guidelines and workflows for programmatically reviewing pull requests and creating pending reviews with inline comments using the GitHub CLI and REST API. Use this when instructed to review a PR or when providing feedback.
---

# Pull request reviewer guidelines

Follow these guidelines when reviewing pull requests programmatically.

## Creating a pending PR review with inline comments

The GitHub REST API supports creating a pending review with all comments in one call.
The key is to omit the `event` field.
This defaults the review to `PENDING` state.

Get the HEAD commit SHA using the GitHub CLI.
```bash
gh api repos/OWNER/REPO/pulls/PR_NUMBER --jq '.head.sha'
```

Create a JSON file with the review body and all inline comments.
```json
{
  "commit_id": "<HEAD_SHA>",
  "body": "Overall review summary here.",
  "comments": [
    {
      "path": "path/to/file.ts",
      "line": 42,
      "body": "Review comment here."
    },
    {
      "path": "path/to/other-file.ts",
      "line": 10,
      "body": "Another comment."
    }
  ]
}
```

Create the pending review using the JSON file.
```bash
gh api repos/OWNER/REPO/pulls/PR_NUMBER/reviews \
  --method POST \
  --input review.json \
  --jq '{id: .id, state: .state}'
```
This returns the review ID and state, for example `{"id": 123456, "state": "PENDING"}`.

Submit the review when ready using the review ID.
```bash
gh api repos/OWNER/REPO/pulls/PR_NUMBER/reviews/REVIEW_ID/events \
  --method POST \
  -f event=REQUEST_CHANGES \
  -f body="Please address the inline comments."
```
Valid event values are `APPROVE`, `REQUEST_CHANGES`, and `COMMENT`.

## Known limitations

The API does not support incrementally adding comments to an existing pending review after creation.
All comments must be provided in the initial creation call.
Attempting to create a second pending review while one exists returns a 422 error.
This is a known gap between the web UI and the API.
See https://github.com/orgs/community/discussions/168380 for more details.
To work around this limitation, collect all comments first.
Then create the pending review in one call.

## Comment positioning

Use `line` for single-line comments.
The `line` refers to the line number in the file, not the diff.
Use `start_line` and `line` for multi-line comments.
Use `side` set to `LEFT` or `RIGHT` for diff-specific positioning.
Use `subject_type` set to `"file"` for file-level comments.
No line number is needed for file-level comments.
