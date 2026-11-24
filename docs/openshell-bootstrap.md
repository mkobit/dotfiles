# OpenShell host bootstrap and sandbox workflow

This guide covers OpenShell 0.1.9 on WSL 2, credential-free public repository work, and a separate signed push workflow.
Keep the SSH signing private key on the host.
SBX remains available during the pilot.

## 1. Enable and install OpenShell

OpenShell installs only when `[data.local.bin.openshell].installation_method` is `"github_releases"` in the active `chezmoi` configuration.
The base init template enables the MicroVM Gateway only on Linux x86-64 WSL 2 when `wslpath` is available.
An overlay replaces the base init template, so it must declare the installation method and `microvm = true` itself to enable these targets.
The OpenShell CLI supports other platforms, but this managed MicroVM service uses Linux x86-64 binaries.

Run `chezmoi init` to select the OpenShell installation method.
The generated configuration must keep the setting at `"none"` on unsupported hosts.

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

The WSL x86-64 pilot passed with OpenShell 0.1.9 and `nvcr.io/nvidia/base/ubuntu@sha256:494398fac1b07614c63ba179e3558d84a5a9ce19a6374560ceac04d822462e45`.
The guest supervisor became ready and `id` returned exit code 0 as `uid=1000(ubuntu)`.
A separate strict-policy check confirmed that `/tmp` is writable, `/etc` writes are denied, and the guest has no Docker socket, `/dev/kvm`, or `/mnt/c` mount.
The `--no-keep` option removes the smoke sandbox after completion.
The stock guest does not include Git, so this smoke test does not validate the `/sandbox` image or Git operations.
CI does not cover nested WSL MicroVM execution.

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
openshell sandbox create -g openshell-microvm --name dotfiles-read \
  --from dotfiles-openshell-sandbox:local --policy "$read_policy" \
  --detach --no-auto-providers -- sleep 3600
rm -f "$read_policy"
trap - EXIT
openshell sandbox exec -g openshell-microvm dotfiles-read -- sh -ec '
  git clone --no-checkout https://github.com/mkobit/dotfiles.git /tmp/dotfiles
  git -C /tmp/dotfiles fetch --no-tags origin "$1"
  git -C /tmp/dotfiles checkout --detach "$2"
  test "$(git -C /tmp/dotfiles rev-parse HEAD)" = "$2"
' sh "$REVIEWED_REF" "$REVIEWED_COMMIT"
```

This path does not use GitHub authentication.
Use a separate approved model provider if the coding agent needs model access.
The repository clone lives in writable `/tmp`.
Delete only the `dotfiles-read` sandbox after the task.

## 5. Prepare a host-signed bundle for offline transfer

Use Git bundles only when you need to transfer host-signed commits or work without public Git access.
Do not copy or mount the SSH signing private key into the sandbox.
Register its public key on GitHub as a **Signing Key only** and add it to the host's `allowed_signers` file.

Create bundles from a host clone that contains the intended base and signed feature branch.
Configure Git's `gpg.ssh.allowedSignersFile` on the host.
Check that the branch contains only the intended commits and verify its signature before creating the bundles.

```bash
git -C /path/to/dotfiles verify-commit test/openshell-signed-push
git -C /path/to/dotfiles bundle create /path/to/dotfiles.bundle main
git -C /path/to/dotfiles bundle create /path/to/signed.bundle test/openshell-signed-push
```

The sandbox uses `GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig`.
With no signing key configured there, commit and tag signing are disabled.
The host must verify the fetched commit signature before review or merge.

## 6. Push a signed bundle with an explicit provider

This section is only for a deliberate push test.
The policy in `docker/openshell/github-push.yaml` allows Git smart-HTTP requests to `mkobit/dotfiles`.
It adds only the `git-receive-pack` request to the public read-only rules.
The existing `.openshell/policy.yaml` remains unchanged and is not compatible with this OpenShell 0.1.9 Gateway because its `process.seccomp` setting is rejected.
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

Start a fresh sandbox for the push.
Pass the provider explicitly and disable automatic provider attachment.

```bash
openshell sandbox create -g openshell-microvm --name signed-push \
  --from dotfiles-openshell-sandbox:local \
  --policy docker/openshell/github-push.yaml \
  --provider rollout-github --detach --no-auto-providers -- sleep 3600
openshell sandbox upload -g openshell-microvm --no-git-ignore signed-push \
  /path/to/dotfiles.bundle /tmp/dotfiles.bundle
openshell sandbox upload -g openshell-microvm --no-git-ignore signed-push \
  /path/to/signed.bundle /tmp/signed.bundle
openshell sandbox exec -g openshell-microvm signed-push -- sh -ec '
  ref=refs/heads/test/openshell-signed-push
  git clone --no-checkout /tmp/dotfiles.bundle /tmp/dotfiles
  git -C /tmp/dotfiles fetch /tmp/signed.bundle "$ref:$ref"
  auth=$(printf "%s" "x-access-token:${GITHUB_TOKEN:?provider missing}" | base64 -w 0)
  GIT_AUTH_HEADER="Authorization: Basic $auth" \
    GIT_TERMINAL_PROMPT=0 git -C /tmp/dotfiles \
    --config-env=http.extraHeader=GIT_AUTH_HEADER push \
    https://github.com/mkobit/dotfiles.git "$ref:$ref"
'
```

Do not enable shell tracing or put a token in the remote URL or command.
The OpenShell proxy substitutes the provider placeholder in the Authorization header.
The sandbox cannot sign new commits because it has no private signing key.
The previous pilot pushed commit `4976d176`. The host and GitHub verified its signature.
Verify each new push before review or merge.

```bash
git fetch origin test/openshell-signed-push
git log --show-signature FETCH_HEAD -n 1
git verify-commit FETCH_HEAD
commit_sha="$(git rev-parse FETCH_HEAD)"
gh api "repos/mkobit/dotfiles/commits/${commit_sha}" --jq .commit.verification.verified
```

## 7. Remove pilot state

Delete only the test sandboxes created by these examples and the local provider when the push test ends.
Provider deletion removes the Gateway's copy of the PAT.
Revoke the PAT separately in GitHub if it is no longer needed.
These actions do not affect the managed Gateway service.

```bash
openshell sandbox delete -g openshell-microvm dotfiles-read
openshell sandbox delete -g openshell-microvm signed-push
openshell provider delete -g openshell-microvm rollout-github
```

The stock smoke sandbox uses `--no-keep` and is removed automatically.
To remove the Gateway CLI registration, run `openshell gateway remove openshell-microvm`.
This removes only the registration; it does not stop the service or delete Gateway state, certificates, or providers.
To stop the managed service, run `systemctl --user disable --now openshell-microvm.service`.
Inspect `~/.local/state/openshell-microvm/` before deleting persisted Gateway data.

[OpenShell 0.1.9 GitHub provider and push tutorial](https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access)
[OpenShell 0.1.9 MicroVM configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)
[OpenShell 0.1.9 provider credential injection](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/overview#how-credential-injection-works)
