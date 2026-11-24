-- Reusable Hammerspoon actions.
local M = {}

local function isWord(char)
    return char and char:match("^[A-Za-z0-9_-]$") ~= nil
end

-- Accessibility ranges use UTF-16 code units, not Lua byte offsets.
function M.plan(text, location, length)
    if type(text) ~= "string" or math.type(location) ~= "integer" or math.type(length) ~= "integer"
        or location < 0 or length < 0 then return nil end
    local chars, offsets, bytes = {}, {}, {}
    local units = 0
    local ok = pcall(function()
        for byte, codepoint in utf8.codes(text) do
            local i = #chars + 1
            chars[i] = utf8.char(codepoint)
            offsets[i] = units
            bytes[i] = byte
            units = units + (codepoint > 0xffff and 2 or 1)
        end
    end)
    if not ok then return nil end
    offsets[#chars + 1], bytes[#chars + 1] = units, #text + 1
    -- Reject ranges that split a UTF-16 character.
    local first, last
    for i, offset in ipairs(offsets) do
        if offset == location then first = i end
        if offset == location + length then last = i end
    end
    if not first or not last then return nil end
    -- Expand the word at the caret, or the partial words at each selection edge.
    if length == 0 then
        while first > 1 and isWord(chars[first - 1]) do first = first - 1 end
        while last <= #chars and isWord(chars[last]) do last = last + 1 end
    else
        if isWord(chars[first]) then
            while first > 1 and isWord(chars[first - 1]) do first = first - 1 end
        end
        if isWord(chars[last - 1]) then
            while last <= #chars and isWord(chars[last]) do last = last + 1 end
        end
    end
    -- Do not split a word that contains characters outside the supported alphabet.
    if (chars[first - 1] and utf8.codepoint(chars[first - 1]) > 127)
        or (chars[last] and utf8.codepoint(chars[last]) > 127) then return nil end
    -- Convert spaces and tabs to hyphens and require an XML-style name.
    local name = text:sub(bytes[first], bytes[last] - 1):gsub("[ \t]+", "-")
    if not name:match("^[A-Za-z_][A-Za-z0-9_-]*$") then return nil end
    local open, close = "<" .. name .. ">", "</" .. name .. ">"
    local before, after = text:sub(1, bytes[first] - 1), text:sub(bytes[last])
    -- Put the caret between the opening and closing tags. The tag is ASCII.
    return {
        location = offsets[first], length = offsets[last] - offsets[first],
        replacement = open .. close, cursor = offsets[first] + #open,
        value = before .. open .. close .. after, before = before, after = after,
    }
end

local function sameRange(a, b)
    return type(a) == "table" and type(b) == "table"
        and a.location == b.location and a.length == b.length
end

-- Keep timers alive while accessibility changes are pending.
local activeTimers = {}
local pending = false

local function waitFor(api, check, complete, fail)
    local attempts = 0
    local function schedule(fn)
        local timer
        local ok, result = pcall(api.timer.doAfter, 0.05, function()
            activeTimers[timer] = nil
            fn()
        end)
        if not ok or not result then return false end
        timer = result
        activeTimers[timer] = true
        return true
    end
    local function poll()
        local ok, status = pcall(check)
        if ok and status == "ready" then
            local finished, err = pcall(complete)
            if finished and err ~= false then return end
        elseif ok and status == "wait" and attempts < 20 then
            attempts = attempts + 1
            if schedule(poll) then return end
        end
        fail()
    end
    return schedule(poll)
end

-- Some fields cannot write AXSelectedText; type into the selected range instead.
local function typeReplacement(api, system, element, app, value, range, expanded, plan)
    if not api.timer or not api.timer.doAfter or not api.eventtap or not api.eventtap.keyStrokes then return false end
    if not element:setAttributeValue("AXSelectedTextRange", expanded) then return false end
    local typed = false
    local function fail()
        pending = false
        api.alert.show(typed and "Could not verify tag insertion; text may have changed"
            or "Cannot wrap text in this field")
    end
    -- Wait for each selection and text change; stop if focus or text changes unexpectedly.
    local scheduled = waitFor(api, function()
        if system:attributeValue("AXFocusedUIElement") ~= element or element:attributeValue("AXValue") ~= value then
            return "stop"
        end
        local current = element:attributeValue("AXSelectedTextRange")
        if sameRange(current, expanded) then return "ready" end
        if sameRange(current, range) then return "wait" end
        return "stop"
    end, function()
        if system:attributeValue("AXFocusedUIElement") ~= element or element:attributeValue("AXValue") ~= value
            or not sameRange(element:attributeValue("AXSelectedTextRange"), expanded) then return false end
        typed = true
        api.eventtap.keyStrokes(plan.replacement, app)
        return waitFor(api, function()
            if system:attributeValue("AXFocusedUIElement") ~= element then return "stop" end
            local current = element:attributeValue("AXValue")
            if current == plan.value then return "ready" end
            if current == value then return "wait" end
            if type(current) ~= "string" or current:sub(1, #plan.before) ~= plan.before
                or (#plan.after > 0 and current:sub(-#plan.after) ~= plan.after) then return "stop" end
            local inserted = current:sub(#plan.before + 1, #current - #plan.after)
            if plan.replacement:sub(1, #inserted) == inserted then return "wait" end
            return "stop"
        end, function()
            local insertedEnd = { location = plan.location + #plan.replacement, length = 0 }
            return waitFor(api, function()
                if system:attributeValue("AXFocusedUIElement") ~= element
                    or element:attributeValue("AXValue") ~= plan.value then return "stop" end
                local current = element:attributeValue("AXSelectedTextRange")
                if sameRange(current, insertedEnd) then return "ready" end
                if sameRange(current, expanded) then return "wait" end
                return "stop"
            end, function()
                if system:attributeValue("AXFocusedUIElement") ~= element
                    or element:attributeValue("AXValue") ~= plan.value
                    or not sameRange(element:attributeValue("AXSelectedTextRange"), insertedEnd) then return false end
                local cursor = { location = plan.cursor, length = 0 }
                if not element:setAttributeValue("AXSelectedTextRange", cursor) then return false end
                return waitFor(api, function()
                    if system:attributeValue("AXFocusedUIElement") ~= element
                        or element:attributeValue("AXValue") ~= plan.value then return "stop" end
                    local current = element:attributeValue("AXSelectedTextRange")
                    if sameRange(current, cursor) then return "ready" end
                    if sameRange(current, insertedEnd) then return "wait" end
                    return "stop"
                end, function() pending = false; return true end, fail)
            end, fail)
        end, fail)
    end, fail)
    pending = scheduled
    return scheduled
end

function M.promptTag(api)
    api = api or hs
    if pending then return false end
    local system = api.axuielement.systemWideElement()
    local element = system:attributeValue("AXFocusedUIElement")
    local app = api.application.frontmostApplication()
    -- Ghostty and secure fields do not provide a supported writable text target.
    if not element or not app or app:bundleID() == "com.mitchellh.ghostty" then return false end
    local role, subrole = element:attributeValue("AXRole"), element:attributeValue("AXSubrole")
    if (role ~= "AXTextField" and role ~= "AXTextArea") or subrole == "AXSecureTextField" then return false end
    if not element:isAttributeSettable("AXSelectedTextRange") then return false end
    local selectedTextWritable = element:isAttributeSettable("AXSelectedText")
    if not selectedTextWritable and not element:isAttributeSettable("AXValue") then return false end
    local value, range = element:attributeValue("AXValue"), element:attributeValue("AXSelectedTextRange")
    if type(range) ~= "table" then return false end
    local plan = M.plan(value, range.location, range.length)
    if not plan then return false end
    -- Confirm that focus, text, and selection did not change while planning.
    if system:attributeValue("AXFocusedUIElement") ~= element or element:attributeValue("AXValue") ~= value
        or not sameRange(element:attributeValue("AXSelectedTextRange"), range) then return false end
    local expanded = { location = plan.location, length = plan.length }
    if not selectedTextWritable then
        return typeReplacement(api, system, element, app, value, range, expanded, plan)
    end
    if not element:setAttributeValue("AXSelectedTextRange", expanded)
        or not sameRange(element:attributeValue("AXSelectedTextRange"), expanded)
        or system:attributeValue("AXFocusedUIElement") ~= element or element:attributeValue("AXValue") ~= value then
        if system:attributeValue("AXFocusedUIElement") == element and element:attributeValue("AXValue") == value then
            element:setAttributeValue("AXSelectedTextRange", range)
        end
        return false
    end
    -- Replace only the selected range, then verify the text and caret position.
    local ok, complete = pcall(function()
        local written = element:setAttributeValue("AXSelectedText", plan.replacement)
        if not written or element:attributeValue("AXValue") ~= plan.value
            or system:attributeValue("AXFocusedUIElement") ~= element then
            if system:attributeValue("AXFocusedUIElement") == element and element:attributeValue("AXValue") == value then
                element:setAttributeValue("AXSelectedTextRange", range)
            end
            return false
        end
        local cursor = { location = plan.cursor, length = 0 }
        return element:setAttributeValue("AXSelectedTextRange", cursor) ~= nil
            and sameRange(element:attributeValue("AXSelectedTextRange"), cursor)
    end)
    return ok and complete, not (ok and complete)
end

-- Wrap selected ASCII words (or the word at the cursor); keep the cursor between tags.
-- Example: copied prompt -> <copied-prompt></copied-prompt>.
function M.wrapPromptTag(api)
    api = api or hs
    local ok, result, textMayHaveChanged = pcall(M.promptTag, api)
    if not ok or not result then
        api.alert.show(textMayHaveChanged and "Could not verify tag insertion; text may have changed"
            or "Cannot wrap text in this field")
    end
end

-- Literal insertion needs a focused text field, not a writable AX text value.
-- This also supports terminal input without trying to edit terminal screen text.
function M.insertText(text, api)
    api = api or hs
    if type(text) ~= "string" or text == "" then return false end
    if api.eventtap.isSecureInputEnabled and api.eventtap.isSecureInputEnabled() then return false end
    local app = api.application.frontmostApplication()
    local system = api.axuielement.systemWideElement()
    local element = system:attributeValue("AXFocusedUIElement")
    if not app or not element then return false end
    local role = element:attributeValue("AXRole")
    if (role ~= "AXTextField" and role ~= "AXTextArea")
        or element:attributeValue("AXSubrole") == "AXSecureTextField" then return false end
    if api.application.frontmostApplication() ~= app
        or system:attributeValue("AXFocusedUIElement") ~= element then return false end
    api.eventtap.keyStrokes(text, app)
    return true
end

M.actions = {}

-- Overlays register menu actions before config.lua calls startMenu().
function M.register(title, action)
    M.actions[#M.actions + 1] = { title = title, action = action }
end

-- Put the cursor in the target field before opening the menu.
-- Capture that field and stop if focus cannot be restored.
function M.startMenu(api)
    api = api or hs
    if not api.menubar then return nil end
    local icon = api.image.imageFromPath(api.processInfo.bundlePath .. "/Contents/Resources/statusicon.pdf")
    if not icon then return nil end
    if M.menu then M.menu:delete() end
    M.menu = api.menubar.new()
    if not M.menu then return nil end
    M.menu:setIcon(icon, true)
    M.menu:setMenu(function()
        local app = api.application.frontmostApplication()
        local system = api.axuielement.systemWideElement()
        local element = system:attributeValue("AXFocusedUIElement")
        local items = {}
        for _, entry in ipairs(M.actions) do
            items[#items + 1] = {
                title = entry.title,
                disabled = not app or not element,
                fn = function()
                    local function fail() api.alert.show("Cannot restore the macro text field") end
                    if not app or not element or app:activate() == false then fail(); return end
                    if not waitFor(api, function()
                        if api.application.frontmostApplication() == app
                            and system:attributeValue("AXFocusedUIElement") == element then return "ready" end
                        return "wait"
                    end, function()
                        entry.action(api)
                        return true
                    end, fail) then fail() end
                end,
            }
        end
        items[#items + 1] = { title = "-" }
        items[#items + 1] = { title = "Console", fn = function() api.openConsole() end }
        items[#items + 1] = { title = "Reload config", fn = function() api.reload() end }
        items[#items + 1] = { title = "Preferences", fn = function() api.openPreferences() end }
        return items
    end)
    api.menuIcon(false)
    return M.menu
end

M.register("Wrap prompt tag", M.wrapPromptTag)

return M
