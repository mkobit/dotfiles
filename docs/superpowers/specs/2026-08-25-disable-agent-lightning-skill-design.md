# Disable the Agent Lightning skill

## Goal

Prevent Agent Lightning's generic optimization prompt from being deployed automatically to managed AI tools.

## Change

Keep the pinned `microsoft/agent-lightning` source and checksum in the skill catalog.
Change only its selected skill state from `present` to `absent`.

## Rationale

The upstream repository is primarily a GPU-backed reinforcement-learning framework, not a general coding-agent extension.
Its bundled prompt skill assumes a dedicated agent-evaluation harness and cost-budget artifact.
Leaving it globally enabled adds irrelevant instructions to ordinary Claude, Codex, Cursor, and Antigravity sessions.

## Validation

Render the chezmoi externals configuration and confirm it contains no Agent Lightning skill targets.
Run the skill-filter test suite.
