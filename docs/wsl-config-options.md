# WSL Configuration Options

Based on the Microsoft documentation on WSL configuration, there are two primary configuration files you can manage to optimize your WSL environment:

## 1. `wsl.conf` (Per-distribution configuration)
*   **Location:** `/etc/wsl.conf` inside your Linux distribution.
*   **Purpose:** Manages settings specific to that individual Linux environment (e.g., Ubuntu).

## 2. `.wslconfig` (Global WSL 2 configuration)
*   **Location:** `%UserProfile%\.wslconfig` on the Windows host.
*   **Purpose:** Manages global settings that apply to the underlying WSL 2 Virtual Machine powering all your distributions.

---

## Recommended Useful Options

Here are the most useful options you might consider setting up for a development environment:

### Global Settings (`.wslconfig`)

These affect the VM powering WSL and are highly recommended to prevent WSL from consuming all your host machine's resources.

*   **`memory`** (e.g., `memory=8GB`): Limits the amount of RAM the WSL 2 VM can use. By default, it uses up to 50% of your total Windows memory, which can sometimes starve Windows of resources.
*   **`processors`** (e.g., `processors=4`): Limits the number of CPU cores WSL can use.
*   **`autoMemoryReclaim`** (e.g., `autoMemoryReclaim=dropCache` or `gradual`): *Highly recommended!* This is a newer feature that tells WSL to automatically release cached memory back to Windows when not in use. Without this, the `Vmmem` process can hold onto gigabytes of RAM unnecessarily.
*   **`localhostForwarding`** (`true` by default): Ensures that servers running on `localhost` in WSL are accessible via `localhost` in your Windows browser.
*   **`networkingMode=mirrored`** (Windows 11+): An advanced networking mode that mirrors Windows network interfaces into Linux, improving VPN compatibility, supporting IPv6, and allowing connection to WSL via the host's LAN IP.
*   **`dnsTunneling=true`** (Windows 11+): Changes how DNS requests are proxied from WSL to Windows, greatly improving network reliability when using VPNs.

### Per-Distribution Settings (`wsl.conf`)

*   **`[network] generateHosts = false` / `generateResolvConf = false`**: Useful if you want to use custom DNS settings or a custom `/etc/hosts` file and don't want WSL to overwrite it every time you restart.
*   **`[interop] appendWindowsPath = false`**: By default, WSL appends your entire Windows `PATH` to your Linux `PATH`. Setting this to `false` prevents clutter and stops Linux commands from accidentally running Windows executables (useful if you have tools like `node` installed on both sides).
*   **`[boot] systemd = true`**: Enables `systemd` support in WSL, allowing you to run services like `docker`, `snap`, or `microk8s` natively within WSL.

---

## How to Manage via Chezmoi

If your repository uses Chezmoi to manage dotfiles, here is how you can manage both of these files:

### Managing `wsl.conf` (Inside Linux)
Since it resides in `/etc/`, which is outside your home directory, Chezmoi running as a regular user cannot directly modify it without `sudo`. You typically run a `run_onchange_` or `run_once_` script that copies a template and runs `sudo cp ... /etc/wsl.conf`.

### Managing `.wslconfig` (On Windows from WSL)
Since `.wslconfig` lives in the Windows user profile (`%UserProfile%`), managing it from Chezmoi inside WSL requires resolving the Windows path.
You can create a script (e.g., `run_onchange_wslconfig.sh.tmpl`) in your `.chezmoiscripts/` directory that uses `wslpath -u` to write to the correct Windows location:

```bash
{{- if and (eq .chezmoi.os "linux") (contains "microsoft" (lower .chezmoi.kernel.osrelease)) -}}
#!/usr/bin/env bash
set -euo pipefail

# Get Windows user profile path
WIN_PROFILE=$(cmd.exe /c "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')
WSLCONFIG_PATH=$(wslpath -u "$WIN_PROFILE")/.wslconfig

cat << 'CONFIG_EOF' > "$WSLCONFIG_PATH"
[wsl2]
memory=8GB
processors=4
autoMemoryReclaim=dropCache
localhostForwarding=true

[experimental]
networkingMode=mirrored
dnsTunneling=true
CONFIG_EOF

echo "✅ Updated .wslconfig in Windows User Profile"
{{- end -}}
```

*Note: Changes to `.wslconfig` require completely restarting WSL using `wsl --shutdown` from PowerShell or Cmd for them to take effect.*
