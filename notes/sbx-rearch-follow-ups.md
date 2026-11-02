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
