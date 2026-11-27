---
name: zellij-remote
description: Set up or troubleshoot private remote access to Zellij sessions from a phone or another terminal.
---

# Remote Zellij access

Use the existing host, session, and access method the user selects.
Inspect the installed Zellij and Tailscale versions and their help before proposing commands: `zellij --version`, `zellij web --help`, and `tailscale serve --help`.

## Browser over a private tailnet

1. Check that the host and phone are connected to the same tailnet and that tailnet policy permits access.
   Check the Zellij web server, listener, existing sessions, and sharing settings before making changes.
   The web server defaults to `127.0.0.1:8082`; `web_server` starts the server, while `web_sharing` controls whether new sessions are shared and defaults to `off`.
   Use the share plugin to opt in the intended existing session; the default shortcut is `Ctrl o`, then `s`.
2. Start the web server if needed and authorized, using `zellij web` or the share plugin.
   Create a login token with `zellij web --create-token`, or use the share plugin.
   Check local help before combining token flags: Zellij 0.46 rejects `--create-token` with `--token-name`.
   Tokens appear only once; transfer and store them securely, and use a read-only token when input is not needed.
   An interactive token grants terminal access as the host user.
3. Keep the backend on loopback and use Tailscale Serve for private HTTPS, after checking existing Serve configuration with `tailscale serve status`.
   For example, `tailscale serve --bg 8082` proxies the local port; use the actual listener port and the HTTPS URL from its output.
   Serve is tailnet-only subject to access policy; Funnel exposes a service to the public internet.
   Serve certificate issuance publishes the full DNS name in certificate transparency logs.
   Do not enable Funnel or broaden the listener to a LAN interface for this workflow.
4. On the phone, open the Serve HTTPS URL, authenticate, and attach to the intended shared session.
   Test on cellular data with Wi-Fi off and confirm a harmless input and response in the live agent prompt when the user permits it.
   Avoid entering secrets into the terminal or recording the token in logs or notes.

If Tailscale runs on Windows and Zellij runs in WSL, first check that Windows can reach the WSL loopback listener from Windows; WSL localhost forwarding depends on its networking configuration.
Run Serve on the Windows host only when this path works.

If the phone cannot resolve the tailnet hostname, compare Tailscale connection status, MagicDNS and split DNS settings, and Android Private DNS behavior.
Test DNS and connectivity separately; do not assume Private DNS must be disabled.
If DNS works but access fails, check tailnet policy, Serve status, the local listener, authentication, and whether the intended session is shared.

To end access, stop sharing the selected session or revoke the relevant token through the share plugin or supported CLI flags.
Use `zellij web --stop` when the user intends to stop the server for all web clients.
Remove only the relevant Serve route if requested, after inspecting its configuration.
These actions need not kill the running Zellij session; do not use session-kill commands as cleanup.

## SSH alternative

If the user prefers a terminal and the host already accepts SSH, Termux can attach with a pseudo-terminal, for example `ssh -t <user>@<host> 'zellij attach <session>'`.
Verify host identity and SSH authorization, and use an existing session name to avoid creating or resurrecting an unintended session.

## Mobile keyboard input

The Zellij web client uses `xterm.js` with a hidden `<textarea>` and disables autocomplete/autocorrect, which prevents Gboard swipe typing and voice-to-text from working reliably.
In the browser, tap keys individually or dictate/swipe in another app and paste into the terminal.
In Termux over SSH, swipe horizontally across the extra keys row above the keyboard to open Termux's native Text Input View, where Gboard swipe and voice-to-text work before sending with Enter.

## References

- [Zellij web client](https://zellij.dev/documentation/web-client.html)
- [Zellij options](https://zellij.dev/documentation/options.html)
- [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Tailscale Funnel](https://tailscale.com/docs/reference/tailscale-cli/funnel)
- [WSL networking](https://learn.microsoft.com/windows/wsl/networking)
- [Zellij Android web client typing (#4423)](https://github.com/zellij-org/zellij/issues/4423)
- [Zellij web client IME repeat (#4974)](https://github.com/zellij-org/zellij/issues/4974)
- [xterm.js mobile predictive keyboard (#2403)](https://github.com/xtermjs/xterm.js/issues/2403)
- [xterm.js Android Chrome typing (#3600)](https://github.com/xtermjs/xterm.js/issues/3600)
