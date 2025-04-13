-- Window Management Module

-- Resize window to full screen
function maximizeWindow()
    local win = hs.window.focusedWindow()
    if win then
        win:maximize()
    end
end

-- Resize window to left half of screen
function leftHalfWindow()
    local win = hs.window.focusedWindow()
    if win then
        local f = win:frame()
        local screen = win:screen()
        local max = screen:frame()
        
        f.x = max.x
        f.y = max.y
        f.w = max.w / 2
        f.h = max.h
        win:setFrame(f)
    end
end

-- Resize window to right half of screen
function rightHalfWindow()
    local win = hs.window.focusedWindow()
    if win then
        local f = win:frame()
        local screen = win:screen()
        local max = screen:frame()
        
        f.x = max.x + (max.w / 2)
        f.y = max.y
        f.w = max.w / 2
        f.h = max.h
        win:setFrame(f)
    end
end

-- Window management hotkeys
hs.hotkey.bind({"cmd", "alt", "ctrl"}, "f", maximizeWindow)
hs.hotkey.bind({"cmd", "alt", "ctrl"}, "left", leftHalfWindow)
hs.hotkey.bind({"cmd", "alt", "ctrl"}, "right", rightHalfWindow)

-- Log that the window management module has loaded
print("Window management module loaded")