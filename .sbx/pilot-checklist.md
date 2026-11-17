# Manual pilot checklist

Prepare the two inputs below before the agent starts the live pilot.
Keep private keys, passwords, and tokens out of chat, logs, and the repository.
Use the [approved design](https://github.com/mkobit/dotfiles/blob/c4d122a7/docs/designs/sbx-agy-pilot.md) for the pilot scope.

## 1. Prepare the signing subkey

A signing subkey lets the guest sign Git commits without the primary private key.
Keep the primary private key outside every guest.
Use the [manual GPG guide](README.md#prepare-a-dedicated-gpg-signing-subkey-from-keepass).
Run its commands in one trusted host terminal so the shell variables remain set.

- [ ] [Inspect the KeePass backup](README.md#1-inspect-the-backup).
  Stop if the primary private key is not available.
  Do not use your normal signing key instead.
- [ ] [Create the dedicated signing subkey](README.md#2-create-the-sandbox-subkey).
  Check that the exported copy has no primary private key and only the selected usable private subkey.
- [ ] [Prepare signing without a prompt](README.md#3-prepare-unattended-signing).
  Remove the passphrase only from the isolated copy for the guest.
  Stop if you do not accept that choice.
  This copy can sign for any repository until the subkey expires or you revoke it.
- [ ] [Check signing after a GPG agent restart](README.md#4-check-signing-without-a-cached-passphrase).
  Stop if signing asks for input or fails.
- [ ] [Save the files in a separate KeePass entry](README.md#5-save-and-hand-back-the-selected-subkey).
  Keep the original backup unchanged.
  Give the agent only the public fingerprint and local path to the selected private-subkey file.
  Keep the private setup directory until backup and guest checks finish.

## 2. Identify the existing tracker

A tracker stores the pilot issue and its work status.
A native sync remote is the named destination that the tracker tool uses to exchange state.
The host and guest use the project's sync procedure to get current state and share changes.

- [ ] Give the tracker identity and location.
  Use the existing pilot tracker.
  Do not create another tracker for this setup.
- [ ] Give the native sync remote name and its location.
  Do not include passwords or tokens in the location.
- [ ] Link the project procedure for replica setup, sync, claim, and close.
  If there is no document, give the existing procedure in plain text.
  Do not invent a new procedure.
- [ ] Give the allowed pilot issue or queue scope.
  Include its acceptance criteria or a link to them.
  The guest will select and claim one eligible issue within that scope.

## Return the inputs

Replace the placeholders in this template with the requested information.
Send the file path, never the private-key file contents.
Do not send passwords, tokens, or other secret contents.

```text
Signing subkey fingerprint: <full public fingerprint>
Local private-subkey file path: <absolute path to sandbox-signing.asc>
Tracker identity and location: <existing tracker name and location>
Native sync remote: <remote name and location without credentials>
Tracker procedure: <document link or existing setup, sync, claim, and close steps>
Allowed issue or queue scope: <issue or scope with acceptance criteria>
```

## What the agent does next

The agent copies only the selected private subkey into the guest and sets the exact signing identity.
It checks the usable keys and tests signed commits before and after a guest restart.
It checks tracker access and sync between the host and guest.
It also checks skills, available models, saved-run recovery, and delivery before it claims the live pilot passed.
The guest performs the assigned tracker operations and completes one unit under the approved design.

You may need to complete an interactive GitHub login or register the public certificate.
Use the local login flow if needed.
Register only `public.asc`, never a private-key file.
Do not send a login credential in chat.

After backup and guest checks finish, follow the [protected setup cleanup](README.md#5-save-and-hand-back-the-selected-subkey).
Never remove the original KeePass backup or your normal GnuPG directory.
