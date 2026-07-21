local cfg = _G.DotfilesConfig.chrome.hotkeys.vertical_tabs

local function findSidebarButton(el, depth)
    if depth > 10 then return nil end
    local role  = el:attributeValue("AXRole") or ""
    local label = el:attributeValue("AXDescription") ~= "" and el:attributeValue("AXDescription")
                  or el:attributeValue("AXTitle") or ""
    if role == "AXButton" and (label:find("[Ee]xpand [Tt]abs") or label:find("[Cc]ollapse [Tt]abs")) then
        return el
    end
    for _, child in ipairs(el:attributeValue("AXChildren") or {}) do
        local found = findSidebarButton(child, depth + 1)
        if found then return found end
    end
    return nil
end

local function toggleVerticalTabs()
    local chrome = hs.application.get("com.google.Chrome")
    if not chrome then return end
    local win = chrome:mainWindow()
    if not win then return end
    local btn = findSidebarButton(hs.axuielement.windowElement(win), 0)
    if btn then btn:performAction("AXPress") end
end

local verticalTabsMode = hs.hotkey.modal.new()
verticalTabsMode:bind(cfg.mods, cfg.key, toggleVerticalTabs)

local chromeWatcher = hs.application.watcher.new(function(name, event)
    if name ~= "Google Chrome" then return end
    if event == hs.application.watcher.activated then
        verticalTabsMode:enter()
    elseif event == hs.application.watcher.deactivated then
        verticalTabsMode:exit()
    end
end)
chromeWatcher:start()

local _chrome = hs.application.get("com.google.Chrome")
if _chrome and _chrome:isFrontmost() then
    verticalTabsMode:enter()
end
