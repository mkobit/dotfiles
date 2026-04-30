local WindowManager = {}
WindowManager.__index = WindowManager

-- Configuration
local LOG_TAG = "WindowManager"
local logger = hs.logger.new(LOG_TAG, "info")

-- Constants
local CACHE_DIR_SUBPATH = "hammerspoon/window_manager"
local STATE_FILE_NAME = "window_state.json"

-- Helpers for XDG paths
local function get_cache_dir()
        if _G.DotfilesConfig and _G.DotfilesConfig.cache_dir then
        return _G.DotfilesConfig.cache_dir .. "/" .. CACHE_DIR_SUBPATH
    end

        local xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache and xdg_cache ~= "" then
        return xdg_cache .. "/" .. CACHE_DIR_SUBPATH
    end

        logger:e("Could not determine cache directory. _G.DotfilesConfig.cache_dir and XDG_CACHE_HOME are both unset.")
    return nil
end

local function get_state_file_path()
    local cache_dir = get_cache_dir()
    if not cache_dir then return nil end
    return cache_dir .. "/" .. STATE_FILE_NAME
end

-- Ensure cache directory exists
local function ensure_cache_dir()
    local path = get_cache_dir()
    if not path then return nil end

    local success, err = hs.fs.mkdir(path)
    if not success then
        logger:e("Failed to create cache directory at " .. path .. ": " .. tostring(err))
        hs.alert.show("Error: Could not create window layout cache directory")
        return nil
    end
    return path
end

local caffeinateWatcher = nil
local screenWatcher = nil
local menu = nil
local clearMenuTimer = nil

local function update_status_bar(msg)
    logger:i(msg)

    if not menu then
        menu = hs.menubar.new()
    end

    if menu then
                menu:setTitle("⚡ " .. msg)

                if clearMenuTimer then
            clearMenuTimer:stop()
        end

                clearMenuTimer = hs.timer.doAfter(10, function()
            if menu then
                menu:setTitle("◱")
            end
        end)
    end

        hs.alert.show(msg, {
        strokeColor = {white = 1, alpha = 0.5},
        fillColor = {white = 0.1, alpha = 0.8},
        textColor = {white = 1, alpha = 1},
        strokeWidth = 1,
        radius = 5,
        textSize = 14,
        atScreenEdge = 2, -- Top edge
        fadeInDuration = 0.15,
        fadeOutDuration = 0.15
    }, 3.0)
end
-- --- State Management ---

function WindowManager.get_monitor_setup_id()
    local screens = hs.screen.allScreens()
    local uuids = {}
    for _, s in ipairs(screens) do
        table.insert(uuids, s:getUUID())
    end
    table.sort(uuids)
    return table.concat(uuids, "|")
end

function WindowManager.load_full_state_from_disk()
    local filepath = get_state_file_path()
    if not filepath then return { configurations = {} } end

    local state = hs.json.read(filepath)
    if not state then
        return { configurations = {} }
    end
        if not state.configurations then
        return { configurations = {} }
    end
    return state
end

function WindowManager.save_full_state_to_disk(full_state)
    if not ensure_cache_dir() then return false end
    local filepath = get_state_file_path()
    if not filepath then return false end

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

function WindowManager.capture_window_state()
    logger:i("Capturing window state...")
    local windows = hs.window.filter.default:getWindows()
    local window_data = {}

        for _, win in ipairs(windows) do
        if win:isVisible() and win:isStandard() then
            local app = win:application()
            local screen = win:screen()
            local spaces = hs.window.spaces(win)             local spaceID = nil
            if spaces and #spaces > 0 then
                spaceID = spaces[1]
            end

            local frame = win:frame()
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

function WindowManager.snapshot_current_setup()
    local setup_id = WindowManager.get_monitor_setup_id()
    local current_layout = WindowManager.capture_window_state()

    local full_state = WindowManager.load_full_state_from_disk()
    full_state.configurations[setup_id] = current_layout

    WindowManager.save_full_state_to_disk(full_state)
    hs.alert.show("Window Layout Saved (Setup: " .. #full_state.configurations[setup_id].monitors .. " Monitors)")
end

-- --- Debug View ---

function WindowManager.show_debug_view()
    local setup_id = WindowManager.get_monitor_setup_id()
    local full_state = WindowManager.load_full_state_from_disk()
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
    if WindowManager.debugWebview then
        WindowManager.debugWebview:html(html)
        WindowManager.debugWebview:show()
    else
        WindowManager.debugWebview = hs.webview.new(rect)
        WindowManager.debugWebview:windowStyle({"titled", "closable", "resizable", "utility"})
        WindowManager.debugWebview:allowGestures(true)
        WindowManager.debugWebview:html(html)
        WindowManager.debugWebview:show()
    end
end

-- --- State Restoration ---

function WindowManager.restore_window_state()
    logger:i("Attempting to restore window state...")
    local setup_id = WindowManager.get_monitor_setup_id()
    local full_state = WindowManager.load_full_state_from_disk()

    local saved_config = full_state.configurations[setup_id]

    if not saved_config then
        logger:i("No saved configuration found for this monitor setup (" .. setup_id .. ")")
        hs.alert.show("No layout saved for this monitor setup")
        return
    end

    local current_windows = hs.window.filter.default:getWindows()
    local used_windows = {}
        local windows_by_app = {}
    for _, win in ipairs(current_windows) do
        local appName = win:application() and win:application():name() or "Unknown"
        if not windows_by_app[appName] then windows_by_app[appName] = {} end
        table.insert(windows_by_app[appName], win)
    end

    local windows_to_move = {}

        for _, saved_win in ipairs(saved_config.windows) do
        local matched_win = nil

                local win_by_id = hs.window.get(saved_win.id)
        if win_by_id and win_by_id:id() == saved_win.id then
            matched_win = win_by_id
        end

                if not matched_win and windows_by_app[saved_win.app_name] then
            for _, candidate in ipairs(windows_by_app[saved_win.app_name]) do
                if not used_windows[candidate:id()] and candidate:title() == saved_win.title then
                    matched_win = candidate
                    break
                end
            end
        end

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

        local function process_queue(queue, index)
        if index > #queue then
            hs.alert.show("Window Layout Restored")
            return
        end

        local item = queue[index]
        local win = item.win
        local saved = item.saved

                if saved.space_id then
             local current_space = hs.window.spaces(win)
             if current_space and current_space[1] ~= saved.space_id then
                 if hs.spaces and hs.spaces.moveWindowToSpace then
                     hs.spaces.moveWindowToSpace(win:id(), saved.space_id)
                                          hs.timer.doAfter(0.3, function()
                                                local dest_screen = hs.screen.find(saved.screen_uuid)
                        if dest_screen then
                            win:move(saved.frame, dest_screen, true, 0)
                        end
                                                process_queue(queue, index + 1)
                     end)
                     return                  end
             end
        end

                local dest_screen = hs.screen.find(saved.screen_uuid)
        if dest_screen then
            win:move(saved.frame, dest_screen, true, 0)
        end

                hs.timer.doAfter(0.02, function()
             process_queue(queue, index + 1)
        end)
    end

        process_queue(windows_to_move, 1)
end

-- Configuration flags
WindowManager.config = {
    auto_save_on_lock = true,
    auto_restore_on_wake = false,     auto_restore_on_monitor_change = true
}

function WindowManager.updateMenu()
    if menu then
        menu:setTitle("◱")
        local menu_table = {
            { title = "Snapshot Current Layout", fn = WindowManager.snapshot_current_setup },
            { title = "Restore Layout", fn = WindowManager.restore_window_state },
            { title = "-" },
            { title = "Debug: Show State", fn = WindowManager.show_debug_view },
            { title = "-" },
            { title = "Auto-Save on Lock", checked = WindowManager.config.auto_save_on_lock, fn = function()
                WindowManager.config.auto_save_on_lock = not WindowManager.config.auto_save_on_lock
                WindowManager.updateMenu()
            end },
            { title = "Auto-Restore on Wake", checked = WindowManager.config.auto_restore_on_wake, fn = function()
                WindowManager.config.auto_restore_on_wake = not WindowManager.config.auto_restore_on_wake
                WindowManager.updateMenu()
            end },
             { title = "Auto-Restore on Monitor Change", checked = WindowManager.config.auto_restore_on_monitor_change, fn = function()
                WindowManager.config.auto_restore_on_monitor_change = not WindowManager.config.auto_restore_on_monitor_change
                WindowManager.updateMenu()
            end }
        }
        menu:setMenu(menu_table)
    end
end

local function handle_power_event(eventType)
    local eventName = nil
    if eventType == hs.caffeinate.watcher.screensDidLock then
        eventName = "Screens Locked"
        if WindowManager.config.auto_save_on_lock then
            WindowManager.snapshot_current_setup()
        end
    elseif eventType == hs.caffeinate.watcher.screensDidUnlock then
        eventName = "Screens Unlocked"
    elseif eventType == hs.caffeinate.watcher.screensDidSleep then
        eventName = "Screens Sleeping"
    elseif eventType == hs.caffeinate.watcher.screensDidWake then
        eventName = "Screens Woke Up"
    elseif eventType == hs.caffeinate.watcher.systemDidWake then
        eventName = "System Woke Up"
        if WindowManager.config.auto_restore_on_wake then
            hs.timer.doAfter(2, WindowManager.restore_window_state)
        end
    elseif eventType == hs.caffeinate.watcher.systemWillSleep then
        eventName = "System Sleeping"
    elseif eventType == hs.caffeinate.watcher.sessionDidBecomeActive then
        eventName = "Session Became Active"
    elseif eventType == hs.caffeinate.watcher.sessionDidResignActive then
        eventName = "Session Resigned Active"
    end

    if eventName then
        update_status_bar("Power: " .. eventName)
    end
end

local function handle_screen_event()
    local screens = hs.screen.allScreens()
    local screenCount = #screens

    local msg = string.format("Display: %d screen(s) detected", screenCount)
    update_status_bar(msg)

    for i, screen in ipairs(screens) do
        logger:i(string.format("  Screen %d: %s (%s)", i, screen:name(), screen:id()))
    end

    if WindowManager.config.auto_restore_on_monitor_change then
         hs.timer.doAfter(3, WindowManager.restore_window_state)
    end
end

function WindowManager.start()
        menu = hs.menubar.new()
    WindowManager.updateMenu()

        caffeinateWatcher = hs.caffeinate.watcher.new(handle_power_event)
    caffeinateWatcher:start()

        screenWatcher = hs.screen.watcher.new(handle_screen_event)
    screenWatcher:start()

    logger:i("WindowManager started")
end

return WindowManager
