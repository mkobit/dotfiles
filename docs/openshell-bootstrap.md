# OpenShell host bootstrap and sandbox workflow

This guide covers the supported OpenShell 0.1.9 WSL 2 MicroVM setup, a stock guest smoke test, provider registration, and an isolated-clone Git workflow.
It keeps the signing key on the host and keeps SBX available during the pilot.

## 1. Enable and install OpenShell

OpenShell installs only when `[data.local.bin.openshell].installation_method` is `"github_releases"` in the active `chezmoi` configuration.
The base init template enables the MicroVM Gateway only on Linux x86-64 WSL 2 when `wslpath` is available.
An overlay replaces the base init template, so it must declare the installation method and `microvm = true` itself to enable these targets.

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

The MicroVM Gateway needs read and write access to `/dev/kvm`, `mke2fs`, `debugfs`, and `e2fsck`, plus a reachable Docker engine for local image export.
The managed service listens on `127.0.0.1:17671` and stores Gateway state and TLS certificates under `~/.local/state/openshell-microvm/`.

```bash
systemctl --user daemon-reload
systemctl --user enable --now openshell-microvm.service
OPENSHELL_LOCAL_TLS_DIR=~/.local/state/openshell-microvm/tls \
  openshell gateway add https://127.0.0.1:17671 --local --name openshell-microvm
openshell status -g openshell-microvm
openshell-doctor
```

This setup supports Linux x86-64 WSL 2 only.
It needs `/dev/kvm`, filesystem tools, and a reachable Docker engine.
SBX remains available during the pilot.
Pass `-g openshell-microvm` to Gateway-specific commands when more than one Gateway is registered.
Restart the service after a Gateway or driver update.

```bash
systemctl --user restart openshell-microvm.service
journalctl --user -u openshell-microvm.service
```

## 2. Run the stock guest smoke test

Use the default Ubuntu guest and policy first, with no providers and no host mounts.
This checks Gateway mutual TLS, VM startup, and guest command execution without granting GitHub access.

```bash
openshell sandbox create -g openshell-microvm --name microvm-smoke \
  --no-keep --no-tty --no-auto-providers -- id
```

The WSL x86-64 pilot passed this smoke test with OpenShell 0.1.9 and `nvcr.io/nvidia/base/ubuntu:24.04`.
The guest supervisor became ready and `id` returned exit code 0 as `uid=1000(ubuntu)`.
The `--no-keep` option removed the smoke sandbox after completion.
The managed Gateway service remains active for later testing.
The stock guest does not include Git, so this smoke test does not validate the `/sandbox` image or GitHub push flow.
Two concurrent guest sandboxes also passed on the managed service after an earlier libkrun startup error.
CI does not cover nested WSL MicroVM execution.

## 3. Register the scoped GitHub provider locally

Never put a PAT or LLM API key in `chezmoi.toml` or this repository.
Create a fine-grained PAT for only the target repository.
For the push test, grant **Contents: Read and write** and keep GitHub's default **Metadata: Read-only** permission.
Leave **Pull requests**, **Workflows**, and account permissions at **No access**.
Protect `main` with a GitHub ruleset.

Run these commands in a local Bash or Zsh terminal on the host.
Paste the PAT when `read` waits for input.
The provider command reads the PAT from the environment.

```bash
set +x
IFS= read -rs GITHUB_TOKEN
export GITHUB_TOKEN
openshell provider create -g openshell-microvm --type github \
  --name rollout-github --credential GITHUB_TOKEN
unset GITHUB_TOKEN
openshell provider list -g openshell-microvm --names
```

The provider keeps the credential in the Gateway and substitutes it for approved sandbox requests.

[OpenShell 0.1.9 GitHub provider and push tutorial](https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access)

## 4. Keep commit signing on the host

Keep the dedicated SSH signing private key on the host.
Do not copy or mount it into the sandbox for this rollout.
Register its public key on GitHub as a **Signing Key only** and add it to the host's `allowed_signers` file.

Prepare a signed Git bundle on the host, then upload that bundle into the isolated sandbox clone.
The known staged bundle head is `4976d176` on `test/openshell-signed-push`.
The host verified its SSH signature with `allowedSignersFile`, and the public fingerprint matched a GitHub signing key.
Create bundles from a host clone that contains the intended base and signed feature branch.
Configure the signing public key in Git's `gpg.ssh.allowedSignersFile` on the host and register it as a signing key in GitHub.
Check that the branch contains only the intended commits.
Verify the signature before creating the bundles.

```bash
git -C /path/to/dotfiles verify-commit test/openshell-signed-push
git -C /path/to/dotfiles bundle create /path/to/dotfiles.bundle main
git -C /path/to/dotfiles bundle create /path/to/signed.bundle test/openshell-signed-push
```

The sandbox uses `GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig`.
With no key configured there, commit and tag signing are disabled, so the sandbox can push the already signed bundle without receiving the private signing key.
The host must verify the fetched commit signature before review or merge.

## 5. Build and compose the `/sandbox` image

Sandboxes do not run `chezmoi apply` at runtime because creation-locked filesystem policies and default-deny egress block live downloads and package managers.
Build the reusable `/sandbox` layer from the repository root.

```bash
docker build -f docker/openshell/Dockerfile -t dotfiles-openshell-sandbox:latest .
```

The pilot image booted with `/usr/bin/git` available.
Its detached sandbox accepted both bundles, and the signed bundle fetch resolved to commit `4976d176`.

Compose the layer into a repository sandbox image.

```dockerfile
FROM <repo-base-image>
COPY --from=dotfiles-openshell-sandbox:latest /sandbox /sandbox
ENV HOME=/sandbox \
    PATH="/sandbox/.local/bin:/sandbox/.local/bin/dotfiles:${PATH}" \
    AGY_CLI_DISABLE_AUTO_UPDATE=true \
    GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig
WORKDIR /sandbox/workspace
```

## 6. Create an isolated sandbox and push a signed bundle

Never mount a host `.git` directory or linked worktree as writable into a sandbox.
The repository's existing `.openshell/policy.yaml` is not compatible with this OpenShell 0.1.9 Gateway because its `process.seccomp` setting is rejected.
Save this pilot policy as `github-push.yaml` on the host.
It grants `/usr/bin/git` access to the Git smart-HTTP paths for `mkobit/dotfiles`.

```yaml
version: 1
filesystem_policy:
  include_workdir: true
  read_only:
    - /bin
    - /usr
    - /lib
    - /proc
    - /dev/urandom
    - /etc
    - /var/log
  read_write:
    - /tmp
    - /dev/null
landlock:
  compatibility: best_effort
network_policies:
  dotfiles_push:
    name: dotfiles-push
    endpoints:
      - host: github.com
        port: 443
        protocol: rest
        enforcement: enforce
        rules:
          - allow: {method: GET, path: "/mkobit/dotfiles.git/info/refs*"}
          - allow: {method: POST, path: "/mkobit/dotfiles.git/git-upload-pack"}
          - allow: {method: POST, path: "/mkobit/dotfiles.git/git-receive-pack"}
    binaries:
      - path: /usr/bin/git
```

Use the repository sandbox image for Git operations.
Pass the `rollout-github` provider explicitly.

```bash
openshell sandbox create -g openshell-microvm --name signed-push \
  --from dotfiles-openshell-sandbox:latest --policy /path/to/github-push.yaml \
  --provider rollout-github --detach --no-auto-providers -- sleep 3600
openshell sandbox upload -g openshell-microvm --no-git-ignore signed-push \
  /path/to/dotfiles.bundle /tmp/dotfiles.bundle
openshell sandbox upload -g openshell-microvm --no-git-ignore signed-push \
  /path/to/signed.bundle /tmp/signed.bundle
openshell sandbox exec -g openshell-microvm signed-push -- \
  sh -ec '
    ref=refs/heads/test/openshell-signed-push
    git clone --no-checkout /tmp/dotfiles.bundle /tmp/dotfiles
    git -C /tmp/dotfiles fetch /tmp/signed.bundle "$ref:$ref"
    GIT_AUTH_HEADER="Authorization: Bearer ${GITHUB_TOKEN:?provider missing}" \
      GIT_TERMINAL_PROMPT=0 git -C /tmp/dotfiles \
      --config-env=http.extraHeader=GIT_AUTH_HEADER push \
      https://github.com/mkobit/dotfiles.git "$ref:$ref"
  '
```

Replace the two host bundle paths and policy path with local files.
The first bundle supplies the isolated repository history; the second supplies the signed feature branch.
The provider substitutes the `GITHUB_TOKEN` placeholder in the HTTP Authorization header.
Do not enable shell tracing or put a token in the remote URL or command.
Do not pass a bundle in `--upload` together with a trailing command to `sandbox create`; 0.1.9 requires a separate upload command.
The custom image booted and imported both bundles.
After the push, fetch the branch on the host and verify the same commit in Git and on GitHub.

```bash
git fetch origin test/openshell-signed-push
git log --show-signature FETCH_HEAD -n 1
git verify-commit FETCH_HEAD
commit_sha="$(git rev-parse FETCH_HEAD)"
gh api "repos/mkobit/dotfiles/commits/${commit_sha}" --jq .commit.verification.verified
```

## 7. Stop services and remove pilot state

Remove a Gateway registration with `openshell gateway remove`; this removes the CLI registration only.
It does not stop the service or delete Gateway state, certificates, or provider credentials.
Remove the test sandbox and the locally registered provider when the pilot ends.

```bash
openshell sandbox delete -g openshell-microvm signed-push
openshell provider delete -g openshell-microvm rollout-github
openshell gateway remove openshell-pilot
```

The smoke sandbox was created with `--no-keep` and is removed automatically.
The example removes the separate `openshell-pilot` registration only; keep the active `openshell-microvm` Gateway registered and running.
To stop the managed service, run `systemctl --user disable --now openshell-microvm.service`.
If you also want to delete persisted Gateway data, first inspect `~/.local/state/openshell-microvm/` and remove it only after confirming it contains no state you need.

[OpenShell 0.1.9 MicroVM configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)
[OpenShell 0.1.9 provider credential injection](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/overview#how-credential-injection-works)
