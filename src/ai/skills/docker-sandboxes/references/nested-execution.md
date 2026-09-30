# Nested execution

The host coordinator owns task selection, branch state, review, Git commits, signing, and pushes.

The sandbox runs delegated builds, tests, generators, and inner-agent work.

Host credentials stay on the host.

## Delegation lifecycle

1. Read the repository instructions and select the required command.
2. Run `sbx kit validate .sbx/kit` and `sbx env plan .sbx/sbxenv.yaml`.
3. Run `sbx env create .sbx/sbxenv.yaml`.
4. Delegate a command with `sbx env exec .sbx/sbxenv.yaml -- <command>`.
5. Delegate an interactive harness with `sbx env run .sbx/sbxenv.yaml`.
6. Review the direct-mounted changes and verification output on the host.
7. Commit, sign, and push from the host when authorized.
8. Optionally run `sbx env rm .sbx/sbxenv.yaml --force`.

The standard `clone: false` workspace returns file edits immediately to the host checkout.

Use a private clone only when isolation outweighs that fast review loop and the repository specifies the return path.
