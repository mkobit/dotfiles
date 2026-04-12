{{- if eq .shell "zsh" }}
#compdef obsidian
#
# Obsidian CLI Completion for Zsh
# Provides context-aware auto-completion for the Obsidian CLI.
# Automatically falls back to fzf-tab (if configured) for robust suggestions.

_obsidian_query_cache() {
    local cmd="$1"
    local cache_id="obsidian_${cmd//[^a-zA-Z0-9_]/_}"

    # Simple caching mechanism per-session to prevent slow prompts
    if [[ -z "${(P)cache_id}" ]]; then
        local results
        # Strip potential ansi codes that some CLIs output and return clean lines.
        # Use sed -E for macOS/BSD compatibility instead of sed -r
        results=("${(@f)$(obsidian "$cmd" 2>/dev/null | sed -E 's/\x1B\[[0-9;]*[mK]//g')}")

        # Safely assign the array dynamically without flattening it
        eval "set -A $cache_id \"\${(@)results}\""
    fi
    # Echo array items newline-separated for easy reading
    printf "%s\n" "${(@P)cache_id}"
}

_obsidian() {
    local context state state_descr line
    typeset -A opt_args

    local in_vault=false
    local current_dir="$PWD"

    # Check if we are inside an Obsidian vault
    while [[ "$current_dir" != "/" && -n "$current_dir" ]]; do
        if [[ -d "$current_dir/.obsidian" ]]; then
            in_vault=true
            break
        fi
        current_dir=$(dirname "$current_dir")
    done

    # Define all primary commands of the Obsidian CLI
    local -a commands=(
        "help:Show help"
        "version:Show version"
        "reload:Reload the active window"
        "restart:Restart the app"
        "bases:Commands for Bases plugin"
        "base\:views:List Bases views"
        "base\:create:Create a Bases view"
        "base\:query:Query a Base"
        "bookmarks:Commands for Bookmarks"
        "bookmark:Manage a bookmark"
        "commands:Commands for the Command palette"
        "command:Run a command"
        "hotkeys:Commands for Hotkeys"
        "hotkey:Manage a hotkey"
        "daily:Commands for Daily notes"
        "daily\:path:Get path of daily note"
        "daily\:read:Read daily note"
        "daily\:append:Append to daily note"
        "daily\:prepend:Prepend to daily note"
        "diff:Open file recovery diff"
        "history:Commands for File recovery history"
        "history\:list:List file history"
        "history\:read:Read history entry"
        "history\:restore:Restore history entry"
        "history\:open:Open history entry"
        "file:Commands for managing files"
        "files:List files"
        "folder:Commands for folders"
        "folders:List folders"
        "open:Open a file"
        "create:Create a new file"
        "read:Read a file"
        "append:Append to a file"
        "prepend:Prepend to a file"
        "move:Move a file"
        "rename:Rename a file"
        "delete:Delete a file"
        "backlinks:Commands for Backlinks"
        "links:Commands for Outgoing links"
        "unresolved:Find unresolved links"
        "orphans:Find orphaned files"
        "deadends:Find dead-end files"
        "outline:Commands for Outline"
        "plugins:Commands for Community plugins"
        "plugins\:enabled:List enabled plugins"
        "plugins\:restrict:Manage restricted mode"
        "plugin:Manage a plugin"
        "plugin\:enable:Enable a plugin"
        "plugin\:disable:Disable a plugin"
        "plugin\:install:Install a plugin"
        "plugin\:uninstall:Uninstall a plugin"
        "plugin\:reload:Reload a plugin"
        "aliases:Manage aliases"
        "properties:List properties"
        "property\:set:Set a property"
        "property\:remove:Remove a property"
        "property\:read:Read a property"
        "publish\:site:Publish site info"
        "publish\:list:List published files"
        "publish\:status:Publish status"
        "publish\:add:Add file to publish"
        "publish\:remove:Remove file from publish"
        "publish\:open:Open published file"
        "random:Open random note"
        "random\:read:Read random note"
        "search:Search vault"
        "search\:context:Search context"
        "search\:open:Search and open"
        "sync:Sync commands"
        "sync\:status:Sync status"
        "sync\:history:Sync history"
        "sync\:read:Read sync version"
        "sync\:restore:Restore sync version"
        "sync\:open:Open sync version"
        "sync\:deleted:Sync deleted files"
        "tags:List tags"
        "tag:Manage a tag"
        "tasks:List tasks"
        "task:Manage a task"
        "templates:List templates"
        "template\:read:Read template"
        "template\:insert:Insert template"
        "themes:List themes"
        "theme:Manage theme"
        "theme\:set:Set active theme"
        "theme\:install:Install theme"
        "theme\:uninstall:Uninstall theme"
        "snippets:List snippets"
        "snippets\:enabled:List enabled snippets"
        "snippet\:enable:Enable snippet"
        "snippet\:disable:Disable snippet"
        "unique:Create unique note"
        "vault:Vault info"
        "vaults:List known vaults"
        "vault\:open:Switch to vault"
        "web:Open URL in web viewer"
        "wordcount:Count words and characters"
        "workspace:Workspace tree"
        "workspaces:List saved workspaces"
        "workspace\:save:Save workspace"
        "workspace\:load:Load workspace"
        "workspace\:delete:Delete workspace"
        "tabs:List open tabs"
        "tab\:open:Open new tab"
        "recents:List recently opened files"
        "devtools:Toggle Electron dev tools"
        "dev\:debug:Debugger"
        "dev\:cdp:CDP command"
        "dev\:errors:Show errors"
        "dev\:screenshot:Take screenshot"
        "dev\:console:Show console messages"
        "dev\:css:Inspect CSS"
        "dev\:dom:Query DOM"
        "dev\:mobile:Toggle mobile emulation"
        "eval:Execute JavaScript"
    )

    _arguments -C \
        '1: :->cmds' \
        '2: :->args'

    case $state in
        cmds)
            _describe -t commands "obsidian commands" commands
            ;;
        args)
            local cmd="${words[2]}"

            # Context-aware argument completion based on the subcommand
            case "$cmd" in
                # Property commands
                property\:read|property\:set|property\:remove)
                    if [[ "$in_vault" == "true" ]]; then
                        local props
                        props=("${(@f)$(_obsidian_query_cache "properties")}")
                        if [[ -n "${props[1]}" ]]; then
                            _describe -t properties 'available properties' props
                        fi
                    fi
                    ;;

                # Theme commands
                theme|theme\:set|theme\:uninstall)
                    local themes
                    themes=("${(@f)$(_obsidian_query_cache "themes")}")
                    if [[ -n "${themes[1]}" ]]; then
                        _describe -t themes 'available themes' themes
                    fi
                    ;;

                # Plugin commands
                plugin|plugin\:enable|plugin\:disable|plugin\:reload|plugin\:uninstall)
                    local plugins
                    plugins=("${(@f)$(_obsidian_query_cache "plugins")}")
                    if [[ -n "${plugins[1]}" ]]; then
                        _describe -t plugins 'installed plugins' plugins
                    fi
                    ;;

                # Base commands
                base\:query|base\:views)
                    local bases
                    bases=("${(@f)$(_obsidian_query_cache "bases")}")
                    if [[ -n "${bases[1]}" ]]; then
                        _describe -t bases 'available bases' bases
                    fi
                    ;;

                # Workspace commands
                workspace\:load|workspace\:delete)
                    local workspaces
                    workspaces=("${(@f)$(_obsidian_query_cache "workspaces")}")
                    if [[ -n "${workspaces[1]}" ]]; then
                        _describe -t workspaces 'saved workspaces' workspaces
                    fi
                    ;;

                # Snippet commands
                snippet\:enable|snippet\:disable)
                    local snippets
                    snippets=("${(@f)$(_obsidian_query_cache "snippets")}")
                    if [[ -n "${snippets[1]}" ]]; then
                        _describe -t snippets 'css snippets' snippets
                    fi
                    ;;

                # Template commands
                template\:insert|template\:read)
                    local templates
                    templates=("${(@f)$(_obsidian_query_cache "templates")}")
                    if [[ -n "${templates[1]}" ]]; then
                        _describe -t templates 'templates' templates
                    fi
                    ;;

                # Vault commands
                vault\:open)
                    local vaults
                    vaults=("${(@f)$(_obsidian_query_cache "vaults")}")
                    if [[ -n "${vaults[1]}" ]]; then
                        _describe -t vaults 'known vaults' vaults
                    else
                        _files -/
                    fi
                    ;;

                # File and context operations
                open|read|append|prepend|move|rename|delete|file)
                    if [[ "$in_vault" == "true" ]]; then
                        _files -g "*.md"
                    else
                        _files
                    fi
                    ;;

                *)
                    # Default fallback
                    _files
                    ;;
            esac
            ;;
    esac
}

# Only setup completion if obsidian exists in PATH
if command -v obsidian >/dev/null 2>&1; then
    compdef _obsidian obsidian
fi
{{- end }}
