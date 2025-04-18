-- Placeholder Hammerspoon configuration
-- This is a placeholder file for build purposes only

print("Hammerspoon configuration loaded!")

-- Load modules
local modules = {
    "caffeine",  -- Keep system awake
    "window",    -- Window management
    "reload",    -- Auto reload config
}

for _, module_name in ipairs(modules) do
    local ok, module = pcall(function() 
        return require("modules." .. module_name) 
    end)
    if ok then
        if module and type(module.init) == "function" then
            module.init()
        end
    else
        print("Error loading module: " .. module_name)
        print(module) -- Print the error message
    end
end