local WindowManager = {}
WindowManager.__index = WindowManager

local LOG_TAG = "WindowManager"
local logger = hs.logger.new(LOG_TAG, "info")

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
        -- Set the title to the message
        menu:setTitle("⚡ " .. msg)

        -- Cancel existing timer if any
        if clearMenuTimer then
            clearMenuTimer:stop()
        end

        -- Clear the message after 10 seconds, reverting to just an icon
        clearMenuTimer = hs.timer.doAfter(10, function()
            if menu then
                menu:setTitle("⚡ Events")
            end
        end)
    end

    -- Also show a non-blocking alert
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

function WindowManager.start()
    -- Initialize menu with default title
    menu = hs.menubar.new()
    if menu then
        menu:setTitle("⚡ Events")
    end

    -- Caffeinate Watcher (Sleep/Wake/Lock/Screens)
    caffeinateWatcher = hs.caffeinate.watcher.new(function(eventType)
        local eventName = nil
        if eventType == hs.caffeinate.watcher.screensDidLock then
            eventName = "Screens Locked"
        elseif eventType == hs.caffeinate.watcher.screensDidUnlock then
            eventName = "Screens Unlocked"
        elseif eventType == hs.caffeinate.watcher.screensDidSleep then
            eventName = "Screens Sleeping"
        elseif eventType == hs.caffeinate.watcher.screensDidWake then
            eventName = "Screens Woke Up"
        elseif eventType == hs.caffeinate.watcher.systemDidWake then
            eventName = "System Woke Up"
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
    end)
    caffeinateWatcher:start()

    -- Screen Watcher (Monitor Plug/Unplug/Move)
    screenWatcher = hs.screen.watcher.new(function()
        local screens = hs.screen.allScreens()
        local screenCount = #screens

        local msg = string.format("Display: %d screen(s) detected", screenCount)
        update_status_bar(msg)

        for i, screen in ipairs(screens) do
            logger:i(string.format("  Screen %d: %s (%s)", i, screen:name(), screen:id()))
        end
    end)
    screenWatcher:start()

    logger:i("WindowManager started")
end

return WindowManager
