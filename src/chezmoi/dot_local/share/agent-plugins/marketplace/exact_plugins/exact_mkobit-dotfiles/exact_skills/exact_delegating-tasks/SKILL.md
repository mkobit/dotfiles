---
name: delegating-tasks
description: >-
  Use when a question or follow-up needs research, or when assigning implementation or review to subagents.
---

# Delegate tasks

Before starting a subagent, check that the user request and applicable project and harness rules permit delegation for this task.
Honor requests to work without subagents.
Use only supported delegation tools and pass on only the authority needed for the assignment.
If delegation is unavailable, work directly when permitted and report any required work that remains blocked.

## Research questions

Delegate research by default when a question needs new evidence.
Treat a follow-up that tests a new claim or changes the topic as a new research question.
Answer directly when the conversation or evidence already in hand is sufficient.

- Start with a read-only specialist on the fastest suitable model, such as Luna or Terra where available.
- Give the worker one question or claim to check, the repository or source scope, the available search tools or skills, and a stop condition.
- Ask for a short finding, source links or file and line references, and any gaps or conflicting evidence.
- Use the result to answer or inspect the relevant sources yourself.
- If the evidence is incomplete or the analysis is complex, give a stronger specialist the findings, sources, and remaining question.

For example, for “I thought this code did X,” ask a fast code researcher to find the entry point and one caller or test, and report what the sources show.
If behavior depends on several services or runtime settings, send those findings to a stronger reviewer or trace that path yourself.

## Implementation and review

Assign bounded changes to implementers and choose the least costly specialist who can do the work.
Use a general agent only when no suitable specialist is available.
Give each agent the necessary context, constraints, acceptance criteria, and evidence to return.

Give each implementer exclusive ownership of named files.
Ask implementers to run appropriate checks and fix failures within their scope.
Run independent assignments in parallel when this saves time.
Run coupled or overlapping edits in sequence.
A shared working tree is not an isolated workspace.
Use the repository's available sandbox or workspace isolation.
Verify any required workspace or context separation before assigning work.
For sandboxed work, delegate the full scoped task and inspect outputs on the host before committing or publishing.

Assign review to a separate agent when the risk warrants it or instructions require it.
Give the reviewer the requirements and evidence without the implementer's conclusions.
Keep architecture, branch management, credential-bearing work, final checks, and integration with the root agent.
