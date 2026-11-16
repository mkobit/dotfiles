---
name: repo-bootstrap
description: >-
  Use to prepare a repository for a native SBX task and check guest readiness before work starts.
---

# Repository bootstrap

Read the project instructions, latest-state records, and delegation rules.
Use the repository's tracked SBX environment and kit.
A person or an agent can give the same complete task:

```text
Complete <task> in native SBX.
Scope: <files and limits>.
Branch and base: <branch> from <commit>.
Checks: <required commands>.
Authority: edit/check only; the host owns delivery, signing, and tracker changes.
Return: <report and change location>.
```

Replace the authority line only when the task explicitly assigns more actions.
Follow [repository setup](../sbx-sandboxes/references/repository-setup.md) to create or reuse the guest and verify readiness.
Creation must leave the tools, trust, and frozen dependencies ready.
Do not run manual `mise install`, `mise trust`, or dependency bootstrap to start the task.
Repair the repository kit only within the assigned scope; otherwise report a setup defect and stop.
Do not initialize a tracker.
Use native SBX commands and the repository's checks; no extra task helper is required.
Return the check results and changes to the assigned location.
