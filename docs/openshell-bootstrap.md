# OpenShell host bootstrap and sandbox workflow

This guide covers OpenShell 0.1.9 on WSL 2, public repository work, and guest commit signing with a host-held key.
Use anonymous GitHub access in the guest and publish from the host after verification.

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
Enter the Beads issue ID if the task has one.

The tracked policy permits Git ref discovery and fetch over HTTPS for `mkobit/dotfiles`. [Read-only policy](../docker/openshell/github-read-only.yaml)

```bash
read -r -p 'Reviewed public ref: ' REVIEWED_REF
read -r -p 'Reviewed full commit ID: ' REVIEWED_COMMIT
read -r -p 'Beads issue ID: ' task_bead
[[ "$REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
  printf 'Enter a full 40-character lowercase commit ID.\n' >&2
  exit 2
}
task_sandbox="task-$(python3 -c 'import uuid; print(uuid.uuid4().hex[:12])')" || exit 1
task_labels=(--label repo=dotfiles)
if [ -n "$task_bead" ]; then
  task_labels+=(--label "bead=$task_bead")
fi
openshell sandbox create -g openshell-microvm --name "$task_sandbox" \
  "${task_labels[@]}" \
  --from dotfiles-openshell-sandbox:local \
  --policy docker/openshell/github-read-only.yaml \
  --detach --no-auto-providers -- sleep 3600 || exit 1
if ! openshell sandbox exec -g openshell-microvm "$task_sandbox" -- sh -ec '
  git clone --no-checkout https://github.com/mkobit/dotfiles.git /tmp/dotfiles
  git -C /tmp/dotfiles fetch --no-tags origin "$1"
  git -C /tmp/dotfiles checkout --detach "$2"
  test "$(git -C /tmp/dotfiles rev-parse HEAD)" = "$2"
' sh "$REVIEWED_REF" "$REVIEWED_COMMIT"; then
  printf 'Checkout failed in %s. Inspect the sandbox before starting work.\n' "$task_sandbox" >&2
  exit 1
fi
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
The launcher uses a per-task copy of the tracked Codex provider profile.
Use `openshell profile lint -g openshell-microvm --file docker/openshell/codex-provider-profile.json` to check the profile before import.
Supply the access token on the host when you create a provider. [Codex provider profile](../docker/openshell/codex-provider-profile.json)
The task uses a read-only clone of the pinned `chezmoi-skills` revision and creates one empty, signed commit to check host signing.
The launcher creates a private directory under the OS temporary directory and prints its path.
It keeps logs there and adds `result.bundle` only after it verifies the signed commit and removes the temporary Gateway profile, provider, and sandbox.

## 6. Review and sign a guest commit

Use a dedicated Ed25519 key for guest commits.
Keep the private key on the host and set `signing_key` to its absolute path.
Add a line of the form `agent@example.org namespaces="git" ssh-ed25519 <public-key-data>` to the host's Git `gpg.ssh.allowedSignersFile`.
Use `ssh-keygen -y -f "$signing_key"` to get the public key from the actual host private key.
Use that public key in the allowed signers entry and register it as a GitHub **Signing Key**.
Set `allowed_signers` to the absolute path of the host allowed signers file.
[Git SSH signing settings](https://git-scm.com/docs/git-config#Documentation/git-config.txt-gpgsshprogram)

After the guest finishes its work and checks, stage the intended files in `/tmp/dotfiles`.
Create one unsigned candidate commit.
Set `signing_name`, `signing_email`, and `message` to the intended author name, email, and commit message.

```bash
git -C /tmp/dotfiles -c user.name="$signing_name" -c user.email="$signing_email" \
  commit --no-gpg-sign -m "$message"
```

Run the remaining commands on the host in Bash, except for the guest amend.
Use the trusted full `REVIEWED_COMMIT` from step 4.
Stop if a command block fails.
Use `git fetch` with object validation to import the candidate bundle into a private temporary repository.
Check the sole parent against the trusted base, then review the full diff and commit message.

```bash
review="$(mktemp -d)" &&
  git -C "$review" init --bare &&
  openshell sandbox exec -g openshell-microvm --no-tty --no-login-shell "$task_sandbox" -- \
    git -C /tmp/dotfiles bundle create - HEAD > "$review/candidate.bundle" &&
  git -C "$review" bundle verify "$review/candidate.bundle" &&
  git -C "$review" -c fetch.fsckObjects=true fetch "$review/candidate.bundle" HEAD &&
  test "$(git -C "$review" show -s --format=%P FETCH_HEAD)" = "$REVIEWED_COMMIT" &&
  reviewed_tree="$(git -C "$review" rev-parse 'FETCH_HEAD^{tree}')" &&
  git -C "$review" cat-file commit FETCH_HEAD > "$review/candidate.raw" &&
  sed '1,/^$/d' "$review/candidate.raw" > "$review/candidate.message" &&
  reviewed_message="$(sha256sum < "$review/candidate.message")" &&
  git -C "$review" diff --binary --no-color --no-ext-diff --no-textconv \
    --ignore-submodules=none "$REVIEWED_COMMIT" FETCH_HEAD -- > "$review/candidate.patch" &&
  LC_ALL=C sed -n 'l 0' "$review/candidate.message" "$review/candidate.patch"
```

Continue only if the checks pass and you approve the candidate.
The display marks line ends with `$` and escapes nonprintable bytes.
Run the trusted host signer with the reviewed parent, tree, and exact message hash.
Use the same `signing_name` and `signing_email` as in the candidate.

```bash
python3 docker/openshell/sign-commit.py \
  --gateway openshell-microvm --sandbox "$task_sandbox" --repo /tmp/dotfiles \
  --key "$signing_key" --identity "$signing_name <$signing_email>" \
  --expected-parent "$REVIEWED_COMMIT" --expected-tree "$reviewed_tree" \
  --expected-message-sha256 "${reviewed_message%% *}"
```

When the signer reports that it is ready, amend the candidate in the guest.

```bash
git -C /tmp/dotfiles commit --amend -S --only --reset-author --no-edit --cleanup=verbatim
```

Check that the signer reports success and exits with status 0.
Each signer invocation accepts one request.
Any process that runs as the sandbox user can submit it.
The signer checks the parent, tree, author, committer, and exact message before it releases a signature.

## 7. Verify and publish from the host

Transfer the signed commit into the same host repository.
Check its sole parent, tree, author, committer, and SSH signature.
Compare the signature fingerprint with the fingerprint of the host signing key.
Compare the commit message with the approved message and record the verified commit ID only after all checks pass.

```bash
unset commit_sha
openshell sandbox exec -g openshell-microvm --no-tty --no-login-shell "$task_sandbox" -- \
  git -C /tmp/dotfiles bundle create - HEAD > "$review/signed.bundle" &&
  git -C "$review" bundle verify "$review/signed.bundle" &&
  git -C "$review" -c fetch.fsckObjects=true fetch "$review/signed.bundle" HEAD &&
  test "$(git -C "$review" show -s --format=%P FETCH_HEAD)" = "$REVIEWED_COMMIT" &&
  test "$(git -C "$review" rev-parse 'FETCH_HEAD^{tree}')" = "$reviewed_tree" &&
  git -C "$review" config --local gpg.format ssh &&
  git -C "$review" config --local gpg.ssh.allowedSignersFile "$allowed_signers" &&
  GIT_DIR="$review" git verify-commit FETCH_HEAD &&
  ssh-keygen -y -f "$signing_key" > "$review/signing.pub" &&
  fingerprint="$(ssh-keygen -E sha256 -lf "$review/signing.pub")" &&
  read -r _ signing_fingerprint _ <<< "$fingerprint" &&
  test "$(git -C "$review" show -s --format=%GF FETCH_HEAD)" = "$signing_fingerprint" &&
  identity="$signing_name <$signing_email>" &&
  test "$(git -C "$review" show -s --format='%an <%ae>%n%cn <%ce>' FETCH_HEAD)" = "$identity"$'\n'"$identity" &&
  git -C "$review" cat-file commit FETCH_HEAD > "$review/signed.raw" &&
  sed '1,/^$/d' "$review/signed.raw" > "$review/signed.message" &&
  cmp "$review/candidate.message" "$review/signed.message" &&
  commit_sha="$(git -C "$review" rev-parse FETCH_HEAD)"
```

When publication is authorized, use host Git credentials to push the verified commit ID to the approved feature branch.
Set `feature_ref` to a new full ref under `refs/heads/`.
Check the remote commit ID and GitHub signature before you create a pull request.

```bash
unset published_sha
remote=git@github.com:mkobit/dotfiles.git
test -n "${commit_sha:-}" &&
  test "${feature_ref#refs/heads/}" != "$feature_ref" &&
  test "$feature_ref" != refs/heads/main &&
  git check-ref-format "$feature_ref" &&
  existing_ref="$(git ls-remote --refs "$remote" "$feature_ref")" &&
  test -z "$existing_ref" &&
  git -C "$review" push --force-with-lease="$feature_ref:" "$remote" "$commit_sha:$feature_ref" &&
  test "$(git ls-remote --refs "$remote" "$feature_ref")" = "$commit_sha"$'\t'"$feature_ref" &&
  test "$(gh api "repos/mkobit/dotfiles/commits/${commit_sha}" --jq .commit.verification.verified)" = true &&
  published_sha="$commit_sha"
```

After the remote checks pass, create a draft pull request from the host if authorized.
Set `pr_title` to the title and `pr_body` to the path of the description file.
Check that the draft PR head is the verified commit.

```bash
feature_branch="${feature_ref#refs/heads/}"
test -n "${published_sha:-}" &&
  test "$published_sha" = "$commit_sha" &&
  pr_url="$(gh pr create --repo mkobit/dotfiles --base main --head "$feature_branch" \
    --draft --title "$pr_title" --body-file "$pr_body")" &&
  printf '%s\n' "$pr_url" &&
  test "$(gh pr view "$pr_url" --json headRefOid,isDraft --jq 'select(.isDraft).headRefOid')" = "$commit_sha"
```

## 8. Remove the task sandbox

List the sandboxes for the repository.
Add the bead selector if the task has a Beads issue.
Set `task_sandbox` to the exact name of the sandbox to inspect. [Sandbox labels](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/overview#label-a-sandbox)

```bash
task_selector=repo=dotfiles
if [ -n "${task_bead:-}" ]; then
  task_selector+=",bead=$task_bead"
fi
openshell sandbox list -g openshell-microvm --selector "$task_selector"
openshell sandbox get -g openshell-microvm "$task_sandbox" --output json
```

Delete that sandbox after the task ends and you verify that the reviewed artifact is on the host.
For a failed task, inspect the failure and keep any files or logs you need before you delete the sandbox.
Wait until the task sandbox is absent from `openshell sandbox list -g openshell-microvm`.
The Gateway can accept the delete request before it detaches the provider.
If you created a model provider or profile for this task, set `task_provider` or `task_profile` to its name before cleanup.
Provider deletion removes the Gateway's copy of the credential.
Remove the temporary review directory after you finish using the bundles.

```bash
openshell sandbox delete -g openshell-microvm "$task_sandbox"
openshell sandbox list -g openshell-microvm
```

```bash
if [ -n "${task_provider:-}" ]; then
  openshell provider delete -g openshell-microvm "$task_provider"
fi
if [ -n "${task_profile:-}" ]; then
  openshell profile delete -g openshell-microvm "$task_profile"
fi
if [ -n "${review:-}" ]; then
  rm -r -- "$review"
fi
```

## Optional templates and services

Create a named template if you reuse the same image across tasks. [Sandbox templates](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/templates)

```bash
openshell sandbox template create -g openshell-microvm dotfiles-task \
  --image dotfiles-openshell-sandbox:local
```

In step 4, replace `--from dotfiles-openshell-sandbox:local` with `--template dotfiles-task`.
Keep `--policy` on the sandbox create command.
If a task needs model access, attach its approved provider to that sandbox.
The template can also hold resource limits and non-secret environment settings.
Use a direct launch with `--from` for a task that needs `--env-from`.

Use a named service when a workload already listens on a loopback port inside the sandbox and its Gateway has service routing configured.
Set `task_gateway` to that Gateway's name and `task_sandbox` to the running sandbox name.
This example exposes a process on port 8080 and shows its Gateway URL. [Sandbox services](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/overview#expose-long-running-services)

```bash
openshell service expose -g "$task_gateway" "$task_sandbox" 8080 web
openshell service get -g "$task_gateway" "$task_sandbox" web
```

OpenShell strips incoming `Authorization` headers by default.
Run `openshell service delete -g "$task_gateway" "$task_sandbox" web` when the endpoint is no longer needed.

[OpenShell 0.1.9 GitHub provider and push reference](https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access)
[OpenShell 0.1.9 MicroVM configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)
[OpenShell 0.1.9 provider credential injection](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/overview#how-credential-injection-works)
