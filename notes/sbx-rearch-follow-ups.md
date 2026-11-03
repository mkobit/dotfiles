# SBX workflow manual follow-up work

## Signing and account setup

- Select an existing SSH signing public key or a dedicated GPG signing subkey.
- Register its public key with GitHub if required.
- Confirm that the SBX guest can sign and that GitHub verifies the signature.
- Keep key creation, private-key export, and account changes outside automatic apply.

## Deployment evidence

Record completed and skipped deployment checks here before PR completion.

## Other repositories

Apply and verify this change in dotfiles first.
Then review each repository's tracked kit, verification tasks, Beads storage, branch protection, and signing support before adoption.
Do not change `storagemaxxing`, `canopy`, or an overlay as part of this PR.

## Verified host prerequisites

- `ssh-add -l` failed both with restricted access and approved host access: no authentication agent connection exists.
- Forwarded SSH signing cannot pass a live test until an SSH agent has a selected signing key.
- Existing host signed commits use GPG; this does not prove guest GPG subkey transport.
- `main` has no GitHub branch protection. Add explicit required CI check names to repository workflow configuration before automatic merge.

## Shared kit repositories

Consider a separate kit repository only after the dotfiles kit passes fresh creation tests.
Keep this as follow-up work.
Identify shared runtime inputs, ownership, version pins, and consuming-repository checks before distribution.
Each consuming repository must retain its complete, reproducible environment definition.

Review [sbx/mise-kit](https://hub.docker.com/r/sbx/mise-kit) for adoption across repositories after the dotfiles proof.
Pin the selected artifact and keep each repository's toolchain and checks explicit.

### Mise kit adoption checks

The pinned native mixin is `docker.io/sbx/mise-kit@sha256:21efbf187ee9950b0b3a3bba6d68939bbebe68f853567618536dd9b18a947a59`.
It provides mise `2026.5.2`; the current tested kit uses `2026.10.23`.
It also sets `MISE_TRUSTED_CONFIG_PATHS=/` inside the guest.
Before adoption, test the repository lockfile, task features, trust scope, and fresh creation with the upstream mixin before `./kit`.
Then remove the npm bootstrap and its mise symlink.
Keep the current fresh-tested kit during this implementation.
See [the assessment](sbx-rearch-tasks/mise-kit-assessment.md) for primary sources and exact composition.

## Shared tracker service

Consider a shared Beads HTTP or SQL service only after the host-owned route works.
Verify transport, host service supervision, sandbox network rules, authentication, and Chezmoi convergence first.
Do not infer raw SQL connectivity from an HTTP host-service example.
