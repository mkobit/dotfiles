# macOS destination-alias repair

CI run `41652944917` failed before pytest because the sync hook rejected the macOS `/tmp` ancestor alias.
The repair resolves only the declared destination's parent.
The destination itself and managed descendants retain their symlink checks.
Every other hook byte matches the prior committed implementation.

Five portable temporary-alias tests cover disabled no-op, enabled sync, receipt cleanup, and destination-symlink rejection.
The tests failed before the repair: 3 failed and 2 passed.
After the repair: 5 passed.
The full focused suite passed 142 tests with no skips.
Ruff, real rendering, Bash syntax, and root ShellCheck `0.11.0` passed.
Independent review approved the scoped change.
No active worker remained at handoff.

No real operating-system path, tool, environment setting, or live user destination changed during testing.
Native macOS CI must still confirm the repair.
Detailed local evidence is under `.sbx/task-context/config-task3/macos-fix/`.
See [the root-cause investigation](macos-ci-investigation.md).
