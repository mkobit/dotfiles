# Research and Evaluation: Coding Agent Protocol

**Source:** [Coding Agent Protocol (Gist)](https://gist.github.com/ctoth/d8e629209ff1d9748185b9830fa4e79f)
**Author:** ctoth (GitHub)

## Executive Summary
The "Coding Agent Protocol" proposes a "defensive epistemology" for AI coding agents. It treats code generation not as a creative writing task but as a rigorous engineering process where "reality has hard edges." The core philosophy is that an agent's internal model is often wrong, and it must constantly verify its assumptions against reality (compilers, tests, file systems) before proceeding.

We have evaluated this protocol for use as a global `CLAUDE.md` system prompt.

## Evaluation

### Pros
*   **"Rule 0" (Stop on Failure):** Prevents the common failure mode where an agent blindly retries a failing command, often making the problem worse. It forces a "stop and think" break.
*   **Explicit Reasoning Protocol:** The `DOING` -> `EXPECT` -> `RESULT` loop forces the agent to commit to a prediction *before* taking action. This makes hallucinated expectations obvious when they clash with the actual result.
*   **Epistemic Hygiene:** Explicitly distinguishing between "I believe" (theory) and "I verified" (fact) helps combat confident hallucinations.
*   **Handoff Protocol:** Encourages leaving the context "clean" for the next session (or the next context window), which is crucial for long-running tasks.

### Cons
*   **Verbosity:** The original text is approximately 2,500 words. Including this in every session's system prompt would consume a significant portion of the context window and increase token costs.
*   **Philosophical Overhead:** Much of the text explains *why* the protocol exists (referencing "The Sequences", "Rationality", etc.) rather than *what* to do. An AI agent needs instructions, not persuasion.
*   **Redundancy:** Key points are repeated multiple times for emphasis.

## Decision: Distilled Adoption
We have decided to adopt the **principles** of this protocol but reject the **text**. We have created a distilled version that captures the operational behaviors in a fraction of the space (<10% of the original word count).

### The Distilled Rules
Our `CLAUDE.md` implements the following core behaviors:
1.  **Rule 0:** Stop immediately on failure. Explain, hypothesize, and wait for confirmation.
2.  **Operational Loop:** clearly state `DOING`, `EXPECT`, and `VERIFY` for every action.
3.  **Epistemic Hygiene:** Explicitly mark unverified beliefs.
4.  **Context Discipline:** Periodically re-read the original goal to prevent drift.
5.  **Safety:** "Chesterton's Fence" (don't delete what you don't understand) and irreversibility checks.

This distilled version resides in `src/dot_claude/CLAUDE.md` and is deployed to `~/.claude/CLAUDE.md`.
