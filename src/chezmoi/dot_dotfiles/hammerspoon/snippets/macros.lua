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
    local first, last
    for i, offset in ipairs(offsets) do
        if offset == location then first = i end
        if offset == location + length then last = i end
    end
    if not first or not last then return nil end
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
    local name = text:sub(bytes[first], bytes[last] - 1):gsub("[ \t]+", "-")
    if not name:match("^[A-Za-z_][A-Za-z0-9_-]*$") then return nil end
    local open, close = "<" .. name .. ">", "</" .. name .. ">"
    local before, after = text:sub(1, bytes[first] - 1), text:sub(bytes[last])
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

local function typeReplacement(api, system, element, app, value, range, expanded, plan)
    if not api.timer or not api.timer.doAfter or not api.eventtap or not api.eventtap.keyStrokes then return false end
    if not element:setAttributeValue("AXSelectedTextRange", expanded) then return false end
    local typed = false
    local function fail()
        pending = false
        api.alert.show(typed and "Could not verify tag insertion; text may have changed"
            or "Cannot wrap text in this field")
    end
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

function M.wrapPromptTag(api)
    api = api or hs
    local ok, result, textMayHaveChanged = pcall(M.promptTag, api)
    if not ok or not result then
        api.alert.show(textMayHaveChanged and "Could not verify tag insertion; text may have changed"
            or "Cannot wrap text in this field")
    end
end

return M
