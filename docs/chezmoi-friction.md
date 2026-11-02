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

Authored skills have one source tree under [`src/ai/skills/`](../src/ai/skills/).
The same tree can be required at several tool-specific target paths.
This includes Claude, Codex, Cursor, and a portable plugin package.

Chezmoi supports [external files, archives, and Git repositories](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/).
This repository still needs custom templates to map local authored trees to several target trees.

The [authored skill externals](../src/chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl) scan each source directory and create a file external for each source file and target.
The [file entry template](../src/chezmoi/.chezmoitemplates/ai/authored-file-entry) uses `file://` URLs and a one-second refresh period.
For template files, it starts a child `chezmoi execute-template` command with the parent data.
The [cleanup script](../src/chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-skills-cleanup.sh.tmpl) separately removes files that are no longer selected.
The [archive filter](../src/python/skill_filter/skill_filter/main.py) selects and transforms upstream files for other target trees.

This arrangement keeps one authored source, but spreads mapping, rendering, refresh, and removal rules across several files.
Each additional target also adds external entries and file processing.

### Desired behavior

Declare one source directory and one or more target directories in one place.
Preserve relative paths and executable permissions.
Render selected templates with the normal template data.
Apply selection rules for each target.
Remove obsolete files only within the declared managed scope.
Show the planned copies, changes, and removals through normal `chezmoi diff` and `chezmoi apply`.
Avoid a separate file external and child renderer for each local template copy.
