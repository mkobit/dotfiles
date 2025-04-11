-- Generic platform Neovim settings in Lua
-- Used as a fallback when the specific platform cannot be detected

-- Basic clipboard settings that work on most systems
vim.opt.clipboard = "unnamed,unnamedplus"

-- Font settings for most GUI Neovim instances
if vim.g.neovide or vim.g.gui_vimr or vim.g.fvim_loaded then
  vim.o.guifont = "monospace:h12"
end

-- Support for system commands - use a shell that's likely to be available
if vim.fn.executable('bash') == 1 then
  vim.opt.shell = "bash"
elseif vim.fn.executable('zsh') == 1 then
  vim.opt.shell = "zsh"
end

-- External commands that might be available
if vim.fn.executable('rg') == 1 then
  vim.opt.grepprg = "rg --vimgrep --smart-case --follow"
elseif vim.fn.executable('grep') == 1 then
  vim.opt.grepprg = "grep -n"
end

-- Universal file handling settings
vim.opt.fileformats = "unix,dos,mac"
vim.opt.encoding = "utf-8"
vim.opt.fileencoding = "utf-8"

-- Reasonable defaults for file backup locations
local data_path = vim.fn.stdpath("data")
vim.opt.backupdir = data_path .. "/backup//"
vim.opt.directory = data_path .. "/swap//"
vim.opt.undodir = data_path .. "/undo//"

-- Create directories if they don't exist
for _, dir in ipairs({vim.opt.backupdir:get()[1], vim.opt.directory:get()[1], vim.opt.undodir:get()[1]}) do
  -- Remove trailing //
  dir = dir:gsub('//$', '')
  if vim.fn.isdirectory(dir) == 0 then
    vim.fn.mkdir(dir, "p")
  end
end

-- Universal keymappings that work across platforms
vim.keymap.set('n', '<C-s>', ':write<CR>', { silent = true })
vim.keymap.set('i', '<C-s>', '<Esc>:write<CR>a', { silent = true })

-- Detect terminal capabilities
local function has_feature(x)
  return vim.fn.has(x) == 1
end

-- Terminal feature detection
if has_feature('termguicolors') then
  vim.opt.termguicolors = true
end

-- Minimal plugin setup that should work everywhere
-- Only load if we detect Lua support
if has_feature('nvim-0.5') then
  -- Try to load lazy.nvim but don't fail if it's not available
  local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
  if vim.loop.fs_stat(lazypath) then
    vim.opt.rtp:prepend(lazypath)
    
    local status_ok, lazy = pcall(require, "lazy")
    if status_ok then
      -- Very minimal plugin setup
      lazy.setup({
        -- Only add plugins that are guaranteed to work everywhere
        { "nvim-lua/plenary.nvim" },
        { "folke/tokyonight.nvim", config = function() 
          pcall(function() vim.cmd.colorscheme("tokyonight-night") end)
        end }
      })
    end
  end
end