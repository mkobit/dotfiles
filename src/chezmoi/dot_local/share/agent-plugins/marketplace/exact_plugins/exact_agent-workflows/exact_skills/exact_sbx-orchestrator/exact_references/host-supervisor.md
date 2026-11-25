# Host supervisor contract

The host launches one guest and records the task before launch. Give the guest the complete [task prompt](subagent-task.md). For normal edit/check work, the host retains tracker and delivery authority and receives a patch. For the explicit private-clone pilot, assign the guest the operations to select, claim, complete, deliver, and close one eligible unit.

Record the run identity, effective sandbox name and environment, workspace and baseline, branch when present, prompt, scope, acceptance and exit criteria, return location, coordinator model and thinking effort, session identity, and host and guest log paths. For normal edit/check work, verify the assigned workspace and patch return path; tracker and signing inputs are not required.

For the private-clone pilot, also record eligibility, the existing tracker identity and native latest-state and sync procedure, required remote, setup evidence, allowed operations and available models, and signing-subkey identity. Verify readiness and valid guest Git metadata before pilot launch. Missing pilot inputs block pilot launch; do not invent tracker configuration or initialize a tracker.

Use [worker launch](worker-launch.md) and save the session. The host may stop active observation while this one guest finishes. Do not start a background assignment loop or another guest. Preserve output, exit status, and record. Process exit alone does not prove completion. Use [recovery](recovery.md) after interruption and [delivery](delivery.md) for pilot host context.

## Shared limits

Record the available native guest models and the authorized coordinator model and effort. Keep the coordinator model and session fixed for the run. The guest uses one implementation writer and a separate reviewer. Do not invent tools or require host-specific model names. Stop on authentication, quota, or unavailable-model errors.
