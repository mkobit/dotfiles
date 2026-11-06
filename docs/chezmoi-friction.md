# Chezmoi friction

## Runtime measurements

### Current behavior

A slow `chezmoi apply` can include template processing, external downloads, filters, scripts, and child commands.
The [plugin bridge script](../src/chezmoi/.chezmoiscripts/run_after_agent-plugin-bridge.sh.tmpl) starts a [Python helper](../src/python/skill_filter/skill_filter/plugin_bridge.py) that calls plugin host commands.
The [skill externals](../src/chezmoi/.chezmoiexternals/ai-skills.toml.tmpl) use archive downloads and Python filters.
These operations need separate measurements to identify the cause of a delay.

Chezmoi provides [`--debug`, `--verbose`, and `--progress`](https://www.chezmoi.io/reference/command-line-flags/global/).
Progress output covers external downloads.
The documented [hooks](https://www.chezmoi.io/reference/configuration-file/hooks/) cover commands, Git events, and source-state reads.
The documented events do not include a hook for each script or external.
The interfaces inspected for v2.72.1 did not provide a simple report with elapsed time for each operation.

### Desired behavior

An optional runtime switch should show the active operation and its elapsed time.
The output should identify the script, download, filter, or child command.
A wait for a lock should show the lock path, wait duration, and owner process when that information is available.
A long operation should show that it is still active.
Completion output should show the elapsed time and exit status.
The measurements should work without a terminal and should not require full debug output or script contents.

## Source directory mapping

### Current behavior

Resolved for authored plugins on 2026-11-06.
Each authored plugin is one native source folder under [`exact_plugins/`](../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/), which Claude, Codex, Cursor, and Antigravity share.
Chezmoi renders templates, removes deleted files through `exact_` folders, and shows changes in `chezmoi diff`.
The remaining friction is selection: entries ignored inside an `exact_` folder stay deployed, so a [small script](../src/chezmoi/.chezmoiscripts/run_onchange_before_00-agent-plugin-deselect.sh.tmpl) moves deselected content to a stash and back when it is selected again, because chezmoi prompts when a managed entry was removed outside chezmoi.
The [archive filter](../src/python/skill_filter/skill_filter/main.py) still selects upstream skills.

### Desired behavior

Declare one source directory and one or more target directories in one place.
Preserve relative paths and executable permissions.
Render selected templates with the normal template data.
Apply selection rules for each target.
Remove obsolete files only within the declared managed scope.
Show the planned copies, changes, and removals through normal `chezmoi diff` and `chezmoi apply`.
Avoid a separate file external and child renderer for each local template copy.
