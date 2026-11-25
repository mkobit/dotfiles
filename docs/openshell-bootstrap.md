# OpenShell host bootstrap and sandbox workflow

This guide covers OpenShell 0.1.9 on WSL 2, public repository work, and guest commit signing with a host-held key.
GitHub push requires a separate provider.

## 1. Enable and install OpenShell

OpenShell installs only when `[data.local.bin.openshell].installation_method` is `"github_releases"` in the active `chezmoi` configuration.
The base init template enables the MicroVM Gateway only on Linux x86-64 WSL 2 when `wslpath` is available.
An overlay replaces the base init template, so it must declare the installation method and `microvm = true` itself to enable these targets.
The OpenShell CLI supports other platforms, but this managed MicroVM service uses Linux x86-64 binaries.

Run `chezmoi init` to select the OpenShell installation method.

```bash
chezmoi init
chezmoi diff ~/.local/bin/openshell ~/.local/bin/openshell-doctor \
  ~/.local/bin/openshell-gateway ~/.local/bin/openshell-driver-vm \
  ~/.config/openshell/microvm-gateway.toml ~/.config/systemd
chezmoi apply ~/.local/bin/openshell ~/.local/bin/openshell-doctor \
  ~/.local/bin/openshell-gateway ~/.local/bin/openshell-driver-vm \
  ~/.config/openshell/microvm-gateway.toml ~/.config/systemd
```

The MicroVM Gateway needs `/dev/kvm`, `mke2fs`, `debugfs`, and `e2fsck`, plus a reachable Docker engine for local image export.
The managed service listens on `127.0.0.1:17671` and stores Gateway state and TLS certificates under `~/.local/state/openshell-microvm/`.

```bash
systemctl --user daemon-reload
systemctl --user enable --now openshell-microvm.service
OPENSHELL_LOCAL_TLS_DIR=~/.local/state/openshell-microvm/tls \
  openshell gateway add https://127.0.0.1:17671 --local --name openshell-microvm
openshell status -g openshell-microvm
openshell-doctor
```

Pass `-g openshell-microvm` to Gateway-specific commands when more than one Gateway is registered.
Restart the service after a Gateway or driver update.

```bash
systemctl --user restart openshell-microvm.service
journalctl --user -u openshell-microvm.service
```

## 2. Run the stock guest smoke test

Use the default Ubuntu guest and policy first, with no providers and no host mounts.
This checks Gateway mutual TLS, VM startup, guest command execution, and basic isolation.

```bash
openshell sandbox create -g openshell-microvm --name microvm-smoke \
  --no-keep --no-tty --no-auto-providers -- id
```

Check that `id` reports an unprivileged user and exits with status 0.
The `--no-keep` option removes the smoke sandbox after completion.

## 3. Build the sandbox image from tracked files

Check out the reviewed commit and run this command from the repository root.
Git sends only tracked files to the builder.
The final image includes the rendered sandbox files and the verified chezmoi binary.
Debian packages and some chezmoi externals can still change between builds.

```bash
git archive --format=tar HEAD | docker build --platform linux/amd64 \
  -f docker/openshell/Dockerfile \
  -t dotfiles-openshell-sandbox:local -
```

The image provides `/usr/bin/git` and the `/sandbox` environment.
Use the local tag for this pilot.
Use an immutable registry digest when you reference a published image.
Compose that layer into a repository sandbox image when you need the repository's tools.

```dockerfile
FROM <repo-base-image>
COPY --from=dotfiles-openshell-sandbox:local /sandbox /sandbox
ENV HOME=/sandbox \
    PATH="/sandbox/.local/bin:/sandbox/.local/bin/dotfiles:${PATH}" \
    AGY_CLI_DISABLE_AUTO_UPDATE=true \
    GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig
WORKDIR /sandbox/workspace
```

## 4. Start normal work without GitHub credentials

For normal work on this public repository, clone it over HTTPS without a provider or token.
Use a fresh isolated guest and a read-only Git policy.
Set `REVIEWED_REF` to the public branch or tag that contains the reviewed commit.
Set `REVIEWED_COMMIT` to its full 40-character commit ID.

Create the read-only policy from the push policy by removing its single `git-receive-pack` rule.
This preserves the same filesystem restrictions and permits only public Git fetch requests for this repository.

```bash
read -r -p 'Reviewed public ref: ' REVIEWED_REF
read -r -p 'Reviewed full commit ID: ' REVIEWED_COMMIT
[[ "$REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
  printf 'Enter a full 40-character lowercase commit ID.\n' >&2
  exit 2
}
read_policy="$(mktemp)"
trap 'rm -f "$read_policy"' EXIT
sed '/git-receive-pack/d' docker/openshell/github-push.yaml > "$read_policy"
openshell sandbox create -g openshell-microvm --name dotfiles-task \
  --from dotfiles-openshell-sandbox:local --policy "$read_policy" \
  --detach --no-auto-providers -- sleep 3600
rm -f "$read_policy"
trap - EXIT
openshell sandbox exec -g openshell-microvm dotfiles-task -- sh -ec '
  git clone --no-checkout https://github.com/mkobit/dotfiles.git /tmp/dotfiles
  git -C /tmp/dotfiles fetch --no-tags origin "$1"
  git -C /tmp/dotfiles checkout --detach "$2"
  test "$(git -C /tmp/dotfiles rev-parse HEAD)" = "$2"
' sh "$REVIEWED_REF" "$REVIEWED_COMMIT"
```

This path does not use GitHub authentication.
Use a separate approved model provider if the coding agent needs model access.
The repository clone lives in writable `/tmp`.

## 5. Run the chezmoi-skills pilot

Run the launcher from the repository root after you build or load the pilot image `dotfiles-openshell-sandbox:8a19efcd`.
It uses the existing `openshell-microvm` Gateway by default.
It reads the host Codex ChatGPT login from `CODEX_HOME/auth.json`, or `~/.codex/auth.json` when `CODEX_HOME` is not set.
Use a Codex login that stores credentials in this file.
Set this checkout's `git config user.signingkey` to the path of a readable SSH private key without a passphrase.
The launcher signs as the pilot identity, `Mike Kobit <mkobit@gmail.com>`.

```bash
python3 docker/openshell/run-chezmoi-skills.py
```

Pass `--gateway <name>` to use another registered Gateway.
The task uses a read-only clone of the pinned `chezmoi-skills` revision and creates one empty, signed commit to check host signing.
The launcher creates a private directory under the OS temporary directory and prints its path.
It keeps logs there and adds `result.bundle` only after it verifies the signed commit and removes the temporary Gateway profile, provider, and sandbox.

## 6. Sign a guest commit with a host key

Create a dedicated Ed25519 key for guest commits and keep the private key on the host.
Add a line of the form `agent@example.org namespaces="git" ssh-ed25519 <public-key-data>` to the host's Git `gpg.ssh.allowedSignersFile`.
Register the public key as a GitHub **Signing Key** if you want GitHub to verify pushed commits.
The signer accepts commits whose author and committer both match the configured identity.
[Git SSH signing settings](https://git-scm.com/docs/git-config#Documentation/git-config.txt-gpgsshprogram)

Start the signer on the host for the target guest clone.
It handles one commit request, then exits.

```bash
python3 docker/openshell/sign-commit.py \
  --gateway openshell-microvm --sandbox dotfiles-task --repo /tmp/dotfiles \
  --key /absolute/path/to/host-signing-key \
  --identity 'OpenShell Agent <agent@example.org>'
```

When the signer reports that it is ready, run the commit in the guest.
Stage the intended changes first.
Git fails the signed commit if the signer is unavailable.

```bash
git -C /tmp/dotfiles commit -S -m "Describe the change"
```

Start another signer invocation for each commit.
Run one signer at a time for each clone.
Any process that runs as the sandbox user can submit the one signing request.
The repository path selects the clone to configure.
The signature covers commit data, so enforce repository and branch permissions when you push.

## 7. Push a signed guest commit with an explicit provider

Prepare a push sandbox before you start work if the task authorizes a push.
Use a fine-grained PAT scoped to this repository with **Contents: Read and write** and GitHub's default **Metadata: Read-only** permission.
Leave **Pull requests**, **Workflows**, and account permissions at **No access**.
Protect `main` with a GitHub ruleset.

Register the provider on the selected Gateway only when you need this push workflow.
Enter the PAT at the hidden prompt.
The command receives the value through the environment and names the variable; it does not place the PAT in command history or arguments.

```bash
set +x
IFS= read -rs GITHUB_TOKEN
export GITHUB_TOKEN
openshell provider create -g openshell-microvm --type github \
  --name rollout-github --credential GITHUB_TOKEN
unset GITHUB_TOKEN
openshell provider list -g openshell-microvm --names
```

Use this launch command in place of the read-only launch in section 4.
Run the clone and checkout commands in that sandbox, then sign the commit as in section 5.
The push policy permits Git smart-HTTP requests to `mkobit/dotfiles`.

```bash
openshell sandbox create -g openshell-microvm --name dotfiles-task \
  --from dotfiles-openshell-sandbox:local \
  --policy docker/openshell/github-push.yaml \
  --provider rollout-github --detach --no-auto-providers -- sleep 3600
```

Run this command in the guest to push the signed commit to an authorized feature ref.
The OpenShell proxy substitutes the provider placeholder in the Authorization header.
Keep shell tracing disabled.

```bash
ref=refs/heads/test/openshell-signed-push
auth=$(printf '%s' "x-access-token:${GITHUB_TOKEN:?provider missing}" | base64 -w 0)
GIT_AUTH_HEADER="Authorization: Basic $auth" \
  GIT_TERMINAL_PROMPT=0 git -C /tmp/dotfiles \
  --config-env=http.extraHeader=GIT_AUTH_HEADER push \
  https://github.com/mkobit/dotfiles.git "HEAD:$ref"
```

Verify each new push before review or merge.

```bash
git fetch origin test/openshell-signed-push
git log --show-signature FETCH_HEAD -n 1
git verify-commit FETCH_HEAD
commit_sha="$(git rev-parse FETCH_HEAD)"
gh api "repos/mkobit/dotfiles/commits/${commit_sha}" --jq .commit.verification.verified
```

## 8. Remove the task sandbox

Delete the task sandbox when work ends.
Delete the provider if you created it for this task.
Provider deletion removes the Gateway's copy of the PAT.
Revoke the PAT separately in GitHub if it is no longer needed.
These actions do not affect the managed Gateway service.

```bash
openshell sandbox delete -g openshell-microvm dotfiles-task
openshell provider delete -g openshell-microvm rollout-github
```

[OpenShell 0.1.9 GitHub provider and push tutorial](https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access)
[OpenShell 0.1.9 MicroVM configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)
[OpenShell 0.1.9 provider credential injection](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/overview#how-credential-injection-works)
