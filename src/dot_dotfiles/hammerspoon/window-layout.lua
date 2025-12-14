local WindowLayout = {}
WindowLayout.__index = WindowLayout

-- Configuration
local LOG_TAG = "WindowLayout"
local logger = hs.logger.new(LOG_TAG, "info")

-- Constants
local CACHE_DIR_NAME = "hammerspoon/window_layout"
local STATE_FILE_NAME = "window_state.json"

-- Helpers for XDG paths
local function get_cache_dir()
    -- Priority 1: Configuration override
    if _G.HSConfig and _G.HSConfig.xdg_cache_home then
        return _G.HSConfig.xdg_cache_home .. "/" .. CACHE_DIR_NAME
    end

    -- Priority 2: Environment variable
    local xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache and xdg_cache ~= "" then
        return xdg_cache .. "/" .. CACHE_DIR_NAME
    end

    -- Priority 3: Default fallback
    return os.getenv("HOME") .. "/.cache/" .. CACHE_DIR_NAME
end

local function get_state_file_path()
    return get_cache_dir() .. "/" .. STATE_FILE_NAME
end

-- Ensure cache directory exists
local function ensure_cache_dir()
    local path = get_cache_dir()
    local success, err = hs.fs.mkdir(path)
    if not success then
        logger:e("Failed to create cache directory at " .. path .. ": " .. tostring(err))
        hs.alert.show("Error: Could not create window layout cache directory")
        return nil
    end
    return path
end

-- --- State Management ---

-- Generate a unique ID for the current monitor setup (sorted UUIDs)
function WindowLayout.get_monitor_setup_id()
    local screens = hs.screen.allScreens()
    local uuids = {}
    for _, s in ipairs(screens) do
        table.insert(uuids, s:getUUID())
    end
    table.sort(uuids)
    return table.concat(uuids, "|")
end

function WindowLayout.load_full_state_from_disk()
    local filepath = get_state_file_path()
    local state = hs.json.read(filepath)
    if not state then
        return { configurations = {} }
    end
    -- Migration or fallback if format is old
    if not state.configurations then
        return { configurations = {} }
    end
    return state
end

function WindowLayout.save_full_state_to_disk(full_state)
    if not ensure_cache_dir() then return false end
    local filepath = get_state_file_path()
    if hs.json.write(full_state, filepath, true, true) then
        logger:i("State saved to " .. filepath)
        return true
    else
        logger:e("Failed to save state to " .. filepath)
        hs.alert.show("Error: Failed to save window layout")
        return false
    end
end

-- --- State Capture ---

function WindowLayout.capture_window_state()
    logger:i("Capturing window state...")
    local windows = hs.window.filter.default:getWindows()
    local window_data = {}

    -- Capture Window Data
    for _, win in ipairs(windows) do
        if win:isVisible() and win:isStandard() then
            local app = win:application()
            local screen = win:screen()
            local spaces = hs.window.spaces(win) -- Returns a list of space IDs (usually one)
            local spaceID = nil
            if spaces and #spaces > 0 then
                spaceID = spaces[1]
            end

            local frame = win:frame()
            -- Log detailed window info for debugging
            logger:d(string.format("Captured Window: ID=%d, App=%s, Title=%s, Frame={x=%.1f,y=%.1f,w=%.1f,h=%.1f}, Space=%s",
                win:id(), app and app:name() or "Unknown", win:title(), frame.x, frame.y, frame.w, frame.h, tostring(spaceID)))

            table.insert(window_data, {
                id = win:id(),
                app_name = app and app:name() or "Unknown",
                title = win:title(),
                frame = frame,
                screen_uuid = screen and screen:getUUID() or nil,
                space_id = spaceID
            })
        end
    end

    local monitor_data = {}
    for _, screen in ipairs(hs.screen.allScreens()) do
        local frame = screen:frame()
        logger:d(string.format("Captured Monitor: UUID=%s, Name=%s, Frame={x=%.1f,y=%.1f,w=%.1f,h=%.1f}",
            screen:getUUID(), screen:name(), frame.x, frame.y, frame.w, frame.h))

        table.insert(monitor_data, {
            uuid = screen:getUUID(),
            name = screen:name(),
            frame = frame
        })
    end

    return {
        timestamp = os.time(),
        windows = window_data,
        monitors = monitor_data
    }
end

function WindowLayout.snapshot_current_setup()
    local setup_id = WindowLayout.get_monitor_setup_id()
    local current_layout = WindowLayout.capture_window_state()

    local full_state = WindowLayout.load_full_state_from_disk()
    full_state.configurations[setup_id] = current_layout

    WindowLayout.save_full_state_to_disk(full_state)
    hs.alert.show("Window Layout Saved (Setup: " .. #full_state.configurations[setup_id].monitors .. " Monitors)")
end

-- --- Debug View ---

function WindowLayout.show_debug_view()
    local setup_id = WindowLayout.get_monitor_setup_id()
    local full_state = WindowLayout.load_full_state_from_disk()
    local saved_config = full_state.configurations[setup_id]

    local html = [[
        <html>
        <head>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 20px; font-size: 12px; }
                h1 { font-size: 16px; margin-bottom: 10px; }
                h2 { font-size: 14px; margin-top: 15px; border-bottom: 1px solid #ccc; }
                table { border-collapse: collapse; width: 100%; margin-top: 5px; }
                th, td { text-align: left; padding: 4px; border-bottom: 1px solid #eee; }
                th { background-color: #f5f5f5; }
                .mono { font-family: monospace; }
                .refresh { position: fixed; top: 10px; right: 10px; }
            </style>
            <script>
                setTimeout(function(){ window.location.reload(); }, 2000);
            </script>
        </head>
        <body>
            <div class="refresh">Auto-refresh: 2s</div>
            <h1>Current Monitor Setup ID</h1>
            <div class="mono">]] .. setup_id .. [[</div>

            <h2>Saved State (Disk)</h2>
    ]]

    if saved_config then
        html = html .. "<p>Timestamp: " .. os.date("%Y-%m-%d %H:%M:%S", saved_config.timestamp) .. "</p>"
        html = html .. "<table><tr><th>App</th><th>Title</th><th>Frame</th><th>Space</th></tr>"
        for _, win in ipairs(saved_config.windows) do
            html = html .. string.format("<tr><td>%s</td><td>%s</td><td class='mono'>%.0f,%.0f %.0fx%.0f</td><td>%s</td></tr>",
                win.app_name, win.title:sub(1, 40), win.frame.x, win.frame.y, win.frame.w, win.frame.h, tostring(win.space_id))
        end
        html = html .. "</table>"
    else
        html = html .. "<p>No saved state for this monitor setup.</p>"
    end

    html = html .. "<h2>Current Live Windows</h2><table><tr><th>ID</th><th>App</th><th>Title</th><th>Frame</th></tr>"
    local windows = hs.window.filter.default:getWindows()
    for _, win in ipairs(windows) do
         if win:isVisible() and win:isStandard() then
            local app = win:application()
            local frame = win:frame()
            html = html .. string.format("<tr><td class='mono'>%d</td><td>%s</td><td>%s</td><td class='mono'>%.0f,%.0f %.0fx%.0f</td></tr>",
                win:id(), app and app:name() or "?", win:title():sub(1, 40), frame.x, frame.y, frame.w, frame.h)
         end
    end
    html = html .. "</table></body></html>"

    local rect = hs.geometry.rect(100, 100, 600, 800)
    if WindowLayout.debugWebview then
        WindowLayout.debugWebview:html(html)
        WindowLayout.debugWebview:show()
    else
        WindowLayout.debugWebview = hs.webview.new(rect)
        WindowLayout.debugWebview:windowStyle({"titled", "closable", "resizable", "utility"})
        WindowLayout.debugWebview:allowGestures(true)
        WindowLayout.debugWebview:html(html)
        WindowLayout.debugWebview:show()
    end
end

-- --- State Restoration ---

function WindowLayout.restore_window_state()
    logger:i("Attempting to restore window state...")
    local setup_id = WindowLayout.get_monitor_setup_id()
    local full_state = WindowLayout.load_full_state_from_disk()

    local saved_config = full_state.configurations[setup_id]

    if not saved_config then
        logger:i("No saved configuration found for this monitor setup (" .. setup_id .. ")")
        hs.alert.show("No layout saved for this monitor setup")
        return
    end

    local current_windows = hs.window.filter.default:getWindows()
    local used_windows = {} -- Track which current windows have been moved

    -- Disambiguation Map: AppName -> List of Current Windows
    local windows_by_app = {}
    for _, win in ipairs(current_windows) do
        local appName = win:application() and win:application():name() or "Unknown"
        if not windows_by_app[appName] then windows_by_app[appName] = {} end
        table.insert(windows_by_app[appName], win)
    end

    local windows_to_move = {}

    -- Restoration Matching Logic
    for _, saved_win in ipairs(saved_config.windows) do
        local matched_win = nil

        -- Strategy 1: Match by ID
        local win_by_id = hs.window.get(saved_win.id)
        if win_by_id and win_by_id:id() == saved_win.id then
            matched_win = win_by_id
        end

        -- Strategy 2: Match by App Name + Title
        if not matched_win and windows_by_app[saved_win.app_name] then
            for _, candidate in ipairs(windows_by_app[saved_win.app_name]) do
                if not used_windows[candidate:id()] and candidate:title() == saved_win.title then
                    matched_win = candidate
                    break
                end
            end
        end

        -- Strategy 3: Slot Filling
        if not matched_win and windows_by_app[saved_win.app_name] then
            for _, candidate in ipairs(windows_by_app[saved_win.app_name]) do
                if not used_windows[candidate:id()] then
                    matched_win = candidate
                    break
                end
            end
        end

        if matched_win then
            used_windows[matched_win:id()] = true
            table.insert(windows_to_move, { win = matched_win, saved = saved_win })
        end
    end

    -- Async Restoration Loop to avoid blocking
    -- We define a recursive function to process the list
    local function process_queue(queue, index)
        if index > #queue then
            hs.alert.show("Window Layout Restored")
            return
        end

        local item = queue[index]
        local win = item.win
        local saved = item.saved

        -- Step 1: Move to Space (if needed and supported)
        if saved.space_id then
             local current_space = hs.window.spaces(win)
             if current_space and current_space[1] ~= saved.space_id then
                 if hs.spaces and hs.spaces.moveWindowToSpace then
                     hs.spaces.moveWindowToSpace(win:id(), saved.space_id)
                     -- Spaces move is an animation, we need to wait a bit before moving frame
                     -- or the frame move might get clobbered by the space transition.
                     -- Note: We rely on a timer here because there is no specific "window moved space" event
                     -- that guarantees the animation is complete and the window is ready for frame changes.
                     hs.timer.doAfter(0.3, function()
                        -- Step 2: Move to Screen and Frame (After Space Move)
                        local dest_screen = hs.screen.find(saved.screen_uuid)
                        if dest_screen then
                            win:move(saved.frame, dest_screen, true, 0)
                        end
                        -- Process next window
                        process_queue(queue, index + 1)
                     end)
                     return -- Return here, the next step happens in the callback
                 end
             end
        end

        -- Step 2: Move to Screen and Frame (Immediate if no space move)
        local dest_screen = hs.screen.find(saved.screen_uuid)
        if dest_screen then
            win:move(saved.frame, dest_screen, true, 0)
        end

        -- Process next window immediately (or with tiny delay to be safe)
        hs.timer.doAfter(0.02, function()
             process_queue(queue, index + 1)
        end)
    end

    -- Start the queue
    process_queue(windows_to_move, 1)
end

-- --- UI & Triggers ---

local menu = nil
local caffeinateWatcher = nil
local screenWatcher = nil

-- Configuration flags
WindowLayout.config = {
    auto_save_on_lock = true,
    auto_restore_on_wake = false, -- Default off, user can enable
    auto_restore_on_monitor_change = true
}

function WindowLayout.updateMenu()
    if menu then
        menu:setTitle("◱")
        local menu_table = {
            { title = "Snapshot Current Layout", fn = WindowLayout.snapshot_current_setup },
            { title = "Restore Layout", fn = WindowLayout.restore_window_state },
            { title = "-" },
            { title = "Debug: Show State", fn = WindowLayout.show_debug_view },
            { title = "-" },
            { title = "Auto-Save on Lock", checked = WindowLayout.config.auto_save_on_lock, fn = function()
                WindowLayout.config.auto_save_on_lock = not WindowLayout.config.auto_save_on_lock
                WindowLayout.updateMenu()
            end },
            { title = "Auto-Restore on Wake", checked = WindowLayout.config.auto_restore_on_wake, fn = function()
                WindowLayout.config.auto_restore_on_wake = not WindowLayout.config.auto_restore_on_wake
                WindowLayout.updateMenu()
            end },
             { title = "Auto-Restore on Monitor Change", checked = WindowLayout.config.auto_restore_on_monitor_change, fn = function()
                WindowLayout.config.auto_restore_on_monitor_change = not WindowLayout.config.auto_restore_on_monitor_change
                WindowLayout.updateMenu()
            end }
        }
        menu:setMenu(menu_table)
    end
end

function WindowLayout.start()
    -- Initialize Menu
    menu = hs.menubar.new()
    WindowLayout.updateMenu()

    -- Caffeinate Watcher (Sleep/Wake/Lock)
    caffeinateWatcher = hs.caffeinate.watcher.new(function(eventType)
        if eventType == hs.caffeinate.watcher.screensDidLock and WindowLayout.config.auto_save_on_lock then
            WindowLayout.snapshot_current_setup()
        elseif eventType == hs.caffeinate.watcher.systemDidWake and WindowLayout.config.auto_restore_on_wake then
            -- Delay slightly to allow monitors to wake up
            hs.timer.doAfter(2, WindowLayout.restore_window_state)
        end
    end)
    caffeinateWatcher:start()

    -- Screen Watcher (Monitor Plug/Unplug)
    screenWatcher = hs.screen.watcher.new(function()
        if WindowLayout.config.auto_restore_on_monitor_change then
             -- Debounce or delay to let system settle
             hs.timer.doAfter(3, WindowLayout.restore_window_state)
        end
    end)
    screenWatcher:start()

    logger:i("WindowLayout started")
end

return WindowLayout
