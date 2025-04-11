-- macOS-specific Neovim settings (Lua)

-- macOS clipboard integration
vim.opt.clipboard = "unnamed"

-- GUI Font settings
if vim.g.neovide then
  vim.o.guifont = "JetBrainsMono Nerd Font:h14"
  
  -- Neovide specific settings
  vim.g.neovide_refresh_rate = 120
  vim.g.neovide_cursor_animation_length = 0.05
  vim.g.neovide_cursor_trail_length = 0.3
end

-- Support for system commands
vim.opt.shell = "/bin/zsh"

-- External commands integration
if vim.fn.executable('rg') == 1 then
  vim.opt.grepprg = "rg --vimgrep --smart-case --follow"
end

-- macOS key bindings (using Lua)
local map = vim.keymap.set
map('n', '<D-s>', ':write<CR>', { silent = true })
map({'i', 'c'}, '<D-v>', '<C-R>+', { noremap = true })
map('v', '<D-c>', '"+y', { noremap = true })

-- Check for homebrew packages for language servers
local function has_homebrew_package(pkg)
  local output = vim.fn.system("brew list --formula | grep -q " .. pkg .. " && echo 'yes' || echo 'no'")
  return string.match(output, "yes") ~= nil
end

-- Auto-detect homebrew tools
if has_homebrew_package("pyright") then
  -- Configure pyright if installed via homebrew
  local lspconfig = require('lspconfig')
  lspconfig.pyright.setup{}
end