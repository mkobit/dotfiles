# Global CLAUDE.md memory reference

This document explains the design and sources for our global `CLAUDE.md`, which serves as the core system memory for the agent.

## Sources and inspiration

*   [Coding agent protocol (Gist)](https://gist.github.com/ctoth/d8e629209ff1d9748185b9830fa4e79f)
*   [CLAUDE.md documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/guides/claude-md)
*   [Claude Code memory documentation](https://code.claude.com/docs/en/memory)

## Core principles

We have adopted specific mental models to guide the agent's behavior:

*   **Chesterton's fence**:
    *   [Concept explanation](https://fs.blog/chestertons-fence/)
    *   *Application*: Do not remove code or configuration unless you understand why it was put there in the first place.

*   **Epistemic hygiene**:
    *   Distinguishing between *belief* (unverified theory) and *knowledge* (verified fact).
    *   Explicitly stating "I don't know" rather than hallucinating.

*   **Defensive epistemology**:
    *   Treating code generation as a rigorous engineering process where assumptions must be verified against reality (compilers, tests, file systems).
