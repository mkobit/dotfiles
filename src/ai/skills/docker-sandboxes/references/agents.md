# Agents

Use the native `codex` agent through `.sbx/.sbxenv.yaml`.

Use AGY only through `.sbx/.sbxenv.agy.yaml` until SBX custom-agent environment support is proven on the host.

Before creating an AGY environment, inspect `sbx settings get kit.allowedSources`.

The default allowlist accepts Docker Hub only, so AGY needs the narrow `github.com/shelajev/` source prefix.

Obtain separate confirmation before running `sbx settings set kit.allowedSources '<complete JSON list>'`.

That setting replaces the complete allowlist, so preserve every existing approved entry while adding `github.com/shelajev/`.

Before the first AGY task, confirm the pinned kit source is allowed, create the environment, and run `sbx env exec .sbx/.sbxenv.agy.yaml -- sh -lc 'agy --help < /dev/null'`.

The first AGY run can require a user-completed Google OAuth flow through Docker’s credential proxy.

If SBX cannot resolve `agent: agy`, stop and report the preflight output rather than falling back to a host launcher.

Codex and AGY do not share a persistent sandbox because each environment is created around one agent and maintains separate state.

Use sandbox Git remotes to fetch reviewed clone-mode work back to the host checkout.

Keep sandbox commits unsigned unless a separately approved signing workflow exists on the host.
