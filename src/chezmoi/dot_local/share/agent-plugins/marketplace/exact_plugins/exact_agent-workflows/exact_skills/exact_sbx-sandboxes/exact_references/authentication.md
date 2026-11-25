# Authentication

First check whether the active agent sandbox blocked socket, network, or state access.
The error `docker login service unavailable: cannot determine whether a refresh right now would be safe to guard` can result from those restrictions.
Follow the active tool's escalation policy and retry the failed command before claiming expired authentication or asking the user to log in.
Run `sbx diagnose --format json` with the required platform access to inspect remaining failures.
A restricted diagnosis can hide `/dev/kvm` or suggest a stale socket; those results do not prove a host fault.
Do not restart the daemon or delete sockets based on restricted results.

If any `sbx` command reports `Docker session expired; starting the sign-in flow…`, immediately show the user any verification URL and one-time code from its output.
Tell the user to run `sbx login` in an external terminal pane and complete browser sign-in.
Keep an active login process available while the user completes its sign-in flow.
Do not start repeated unattended login attempts or suppress useful authentication output.
Wait for the user to complete sign-in before retrying dependent work.

Then run `sbx diagnose --format json`.
Inspect the applicable health checks; the number of checks can change.
If authentication or configuration is still incorrect, explain the failed check and ask the user to correct the account or setting.
Resume after the relevant checks pass.

`sbx diagnose --upload` sends diagnostics to Docker support.
Uploading requires separate user authorization and is outside the diagnostic grants.
