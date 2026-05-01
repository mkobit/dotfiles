# Zellij Workspace Layout Automation Plan

## Objective
Create a dynamic Zellij layout using a `chezmoi` template that scans the `~/workspace/mkobit` directory and automatically generates a dedicated tab (with multiple panes) for each project.

## Key Files & Context
- **New File:** `src/chezmoi/dot_config/zellij/layouts/workspace.kdl.tmpl`
- **Context:** Leverages existing Zellij plugin aliases (like `tab-bar` and `status-bar`) defined in `src/chezmoi/.chezmoidata/zellij.toml`.

## Implementation Steps
1. **Create the Layout Template:**
   Create `workspace.kdl.tmpl` with a standard KDL `layout` block.
2. **Define Default Tab:**
   Include a `default_tab_template` containing the `zellij:tab-bar` and `zellij:status-bar` plugins, ensuring consistency with your existing Zellij configuration.
3. **Implement Directory Scanning Logic:**
   - Define a variable for the target directory: `{{ $workspaceDir := joinPath .chezmoi.homeDir "workspace/mkobit" }}`.
   - Use `{{ range (glob (printf "%s/*" $workspaceDir)) }}` to iterate over the contents.
   - Filter for directories using `{{ if (stat .).IsDir }}`.
4. **Generate Tab Definitions:**
   - For each directory, output a `tab` block: `tab name="{{ base . }}" cwd="{{ . }}"`.
   - Within each tab, define a default pane setup (e.g., a vertical split with a large pane for editing and a smaller pane for terminal tasks).

## Verification & Testing
1. **Template Evaluation:** Run `chezmoi execute-template < src/chezmoi/dot_config/zellij/layouts/workspace.kdl.tmpl` to ensure the generated KDL syntax is correct and the directory paths are resolved accurately.
2. **Zellij Load Test:** Apply the changes via `chezmoi apply` and start Zellij with the new layout (`zellij --layout workspace`) to verify tabs and panes are instantiated properly.
