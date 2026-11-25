# Guest task prompt

Give the guest a complete assignment with project instructions, scope, baseline, branch, checks, acceptance criteria, exit criteria, and report location. State the permitted operations, available models, and authority for tracker writes, signing, remote writes, PR, and merge separately. Do not infer authority from credentials. Use [worker handoff](../../worker-handoff/SKILL.md).

For the private-clone pilot, supply the existing tracker identity, native latest-state and sync procedure, eligible queue scope, required remote, setup evidence, assigned dedicated signing subkey, and return location. Grant the guest authority to select, claim, sync, read back, and close one eligible issue, and to complete assigned delivery. Use one implementation subagent and a separate reviewer with available native capabilities. Do not launch a nested sandbox. Stop after one unit and report blockers rather than selecting another.

For the pilot Beads replica, run `bd sync --no-adopt --remote <remote> --json` using the supplied named remote and the [tracker procedure](tracker.md) before reads and after writes. Select one eligible issue, claim it using native operations, sync, and read it back before work. Use the supplied native conflict procedure; do not invent a remote or configuration, initialize a tracker, or overwrite conflicts.

## Read-only task context

For normal edit/check mode, the host supplies task context without guest tracker writes. Use a verified read-only snapshot or supplied prompt, and leave tracker changes to the host. This restriction does not replace explicitly assigned pilot tracker authority.

## Check selection

Run the project checks required by the assignment. Report exact commands, results, failures, skips, and unrun checks. Follow the [delivery procedure](../../worker-handoff/references/delivery.md) only when delivery is explicitly assigned.
