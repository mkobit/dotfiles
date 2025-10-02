-- Hammerspoon configuration entry point
-- Managed by chezmoi

-- Automatic configuration reloading
-- Watches the config directory for .lua file changes and reloads automatically
-- See: https://www.hammerspoon.org/go/#fancyreload
-- See: https://www.hammerspoon.org/docs/hs.html#configdir
function reloadConfig(files)
    local doReload = false
    for _, file in pairs(files) do
        if file:sub(-4) == ".lua" then
            doReload = true
        end
    end
    if doReload then
        hs.reload()
    end
end

-- Use hs.configdir to get the actual configured directory
-- This respects the MJConfigFile preference we set during installation
local configWatcher = hs.pathwatcher.new(hs.configdir, reloadConfig):start()
hs.alert.show("Hammerspoon config loaded")

-- Load the Rectangle Pro API
local RectanglePro = require("rectangle-pro")
