# Nested execution

The host coordinator owns task selection, branch state, review, Git commits, signing, and pushes.

The sandbox runs delegated builds, tests, generators, and inner-agent work.

Host credentials stay on the host.

## Delegation lifecycle

1. Inspect the repository instructions, configuration, required commands, and `sbx ls --format json` output.
2. Reuse an existing matching environment when available.
3. If configuration changed or a new environment is needed, validate the kit and plan the environment.
4. Create the environment only when needed and authorized.
5. Delegate checks with `sbx env exec .sbx/sbxenv.yaml -- <command>`.
6. Review the direct-mounted changes and verification output on the host.
7. Commit, sign, and push from the host when authorized.
8. Remove the environment only when authorized.

The standard `clone: false` workspace returns file edits immediately to the host checkout.

Use a private clone only when isolation outweighs that fast review loop and the repository specifies the return path.
