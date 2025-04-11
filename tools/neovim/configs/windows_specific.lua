-- Windows-specific Neovim settings (Lua)

-- Windows clipboard integration
vim.opt.clipboard = "unnamed"

-- GUI Font settings for Windows
if vim.g.neovide or vim.g.fvim_loaded then
  vim.o.guifont = "JetBrains Mono:h11"
  
  -- Neovide specific settings for Windows
  if vim.g.neovide then
    vim.g.neovide_refresh_rate = 60
    vim.g.neovide_fullscreen = false
    vim.g.neovide_cursor_animation_length = 0.05
    vim.g.neovide_cursor_trail_length = 0.3
  end
end

-- Support for system commands
vim.opt.shell = "cmd.exe"
vim.opt.shellcmdflag = "/c"

-- Windows-specific file paths
local appdata = vim.fn.expand("~/AppData/Local/nvim-data")
vim.opt.backupdir = appdata .. "/backup"
vim.opt.directory = appdata .. "/swap"
vim.opt.undodir = appdata .. "/undo"

-- Create directories if they don't exist
for _, dir in ipairs({vim.opt.backupdir:get()[1], vim.opt.directory:get()[1], vim.opt.undodir:get()[1]}) do
  if vim.fn.isdirectory(dir) == 0 then
    vim.fn.mkdir(dir, "p")
  end
end

-- Use forward slashes instead of backslashes
vim.opt.shellslash = true

-- Fix line endings
vim.opt.fileformats = "dos,unix"

-- External commands on Windows
if vim.fn.executable('rg.exe') == 1 then
  vim.opt.grepprg = "rg.exe --vimgrep --smart-case --follow"
end

-- Windows-specific key bindings
vim.keymap.set('n', '<C-z>', '<Nop>', { noremap = true }) -- Disable suspend on Windows
vim.keymap.set('n', '<C-a>', 'ggVG', { noremap = true }) -- Select all with Ctrl-A

-- PowerShell configuration
if vim.fn.executable('pwsh.exe') == 1 then
  -- Optional: Configure PowerShell integration
  -- vim.opt.shell = "pwsh.exe"
  -- vim.opt.shellcmdflag = "-command"
  
  -- Example of configuring PowerShell-based tools if available
  local has_ps_module = function(module)
    local cmd = string.format('pwsh.exe -NoProfile -Command "if (Get-Module -ListAvailable -Name %s) { exit 0 } else { exit 1 }"', module)
    return os.execute(cmd) == 0
  end
  
  -- Check for PowerShell-based tools
  if has_ps_module("PSScriptAnalyzer") then
    -- Could configure PowerShell language server here
  end
end