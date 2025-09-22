---@class RectanglePro
---@author Jules
---@version 1.0.0
local RectanglePro = {}

---@private
--- Executes a Rectangle Pro action by name.
--- This is a private function used by the public API.
---@param actionName string The name of the action to execute.
---@return boolean, string|nil A tuple where the first element is a boolean indicating success,
---                           and the second is an error message if the action failed.
local function executeAction(actionName)
  if type(actionName) ~= "string" or actionName == "" then
    return false, "actionName must be a non-empty string"
  end

  local url = "rectangle-pro://execute-action?name=" .. actionName
  local ok, err = pcall(hs.urlevent.openURL, url)

  if not ok then
    return false, "Failed to execute Rectangle Pro action: " .. tostring(err)
  end

  return true, nil
end

--- Moves the focused window to the left half of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.leftHalf()
  return executeAction("left-half")
end

--- Moves the focused window to the right half of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.rightHalf()
  return executeAction("right-half")
end

--- Maximizes the focused window.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.maximize()
  return executeAction("maximize")
end

--- Centers the focused window.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.center()
  return executeAction("center")
end

--- Moves the focused window to the top half of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.topHalf()
  return executeAction("top-half")
end

--- Moves the focused window to the bottom half of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.bottomHalf()
  return executeAction("bottom-half")
end

--- Moves the focused window to the first third of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.firstThird()
  return executeAction("first-third")
end

--- Moves the focused window to the first two-thirds of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.firstTwoThirds()
  return executeAction("first-two-thirds")
end

--- Moves the focused window to the last third of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.lastThird()
  return executeAction("last-third")
end

--- Moves the focused window to the last two-thirds of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.lastTwoThirds()
  return executeAction("last-two-thirds")
end

--- Moves the focused window to the top-left quadrant of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.topLeft()
  return executeAction("top-left")
end

--- Moves the focused window to the top-right quadrant of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.topRight()
  return executeAction("top-right")
end

--- Moves the focused window to the bottom-left quadrant of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.bottomLeft()
  return executeAction("bottom-left")
end

--- Moves the focused window to the bottom-right quadrant of the screen.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.bottomRight()
  return executeAction("bottom-right")
end

--- Pins the focused window.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.pin()
  return executeAction("pin")
end

--- Moves the focused window to the next display.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.moveToNextDisplay()
  return executeAction("move-to-next-display")
end

--- Moves the focused window to the previous display.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.moveToPreviousDisplay()
  return executeAction("move-to-previous-display")
end

--- Executes a custom Rectangle Pro layout by name.
---@param layoutName string The name of the custom layout to execute.
---@return boolean, string|nil A tuple indicating success or failure.
function RectanglePro.custom(layoutName)
  return executeAction(layoutName)
end

return RectanglePro
