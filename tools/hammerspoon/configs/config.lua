-- Global configuration options

-- Set animation duration (seconds)
hs.window.animationDuration = 0.1

-- Hide dock icon
hs.dockIcon(false)

-- Default log level
hs.logger.defaultLogLevel = 'info'

-- Console configuration
hs.console.darkMode(true)
hs.console.consoleFont("Menlo", 12)

-- Application watcher
local appWatcher = nil
function applicationWatcher(appName, eventType, appObject)
    if eventType == hs.application.watcher.activated then
        if appName == "Finder" then
            -- Bring all Finder windows forward when one gets activated
            appObject:selectMenuItem({"Window", "Bring All to Front"})
        end
    end
end
appWatcher = hs.application.watcher.new(applicationWatcher)
appWatcher:start()