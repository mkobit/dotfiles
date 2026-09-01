# Agents

Use the native `codex` agent through `.sbx/.sbxenv.yaml`.

Use AGY only through `.sbx/.sbxenv.agy.yaml` until SBX custom-agent environment support is proven on the host.

Before the first AGY task, confirm the pinned kit source is allowed, create the environment, and run `sbx env exec .sbx/.sbxenv.agy.yaml -- sh -lc 'agy --help < /dev/null'`.

The first AGY run can require a user-completed Google OAuth flow through Docker’s credential proxy.

If SBX cannot resolve `agent: agy`, stop and report the preflight output rather than falling back to a host launcher.

Codex and AGY do not share a persistent sandbox because each environment is created around one agent and maintains separate state.

Use sandbox Git remotes to fetch reviewed clone-mode work back to the host checkout.

Keep sandbox commits unsigned unless a separately approved signing workflow exists on the host.
