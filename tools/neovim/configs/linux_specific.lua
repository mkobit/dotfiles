-- Linux-specific Neovim settings (Lua)

-- Linux clipboard integration
if vim.fn.executable('xclip') == 1 then
  vim.opt.clipboard = "unnamedplus"
elseif vim.fn.executable('wl-copy') == 1 and vim.fn.executable('wl-paste') == 1 then
  vim.opt.clipboard = "unnamedplus"
end

-- GUI Font settings for Neovide
if vim.g.neovide then
  vim.o.guifont = "JetBrainsMono Nerd Font:h12"
  
  -- Neovide specific settings for Linux
  vim.g.neovide_refresh_rate = 60
  vim.g.neovide_cursor_animation_length = 0.05
  vim.g.neovide_no_idle = true
end

-- Support for system commands
vim.opt.shell = "/bin/bash"

-- External commands integration
if vim.fn.executable('rg') == 1 then
  vim.opt.grepprg = "rg --vimgrep --smart-case --follow"
end

-- Path settings for Linux
vim.opt.path:append("/usr/include/,/usr/local/include/")

-- Terminal improvements
if vim.env.TERM == "xterm-256color" or vim.env.TERM == "screen-256color" then
  -- Enable true color support
  vim.opt.termguicolors = true
end

-- Auto-detect installed tools on Linux
local function has_apt_package(pkg)
  local output = vim.fn.system("dpkg -l | grep -q " .. pkg .. " && echo 'yes' || echo 'no'")
  return string.match(output, "yes") ~= nil
end

-- Function to check if a command exists
local function command_exists(cmd)
  return vim.fn.executable(cmd) == 1
end

-- Set up LSP servers if available
if command_exists('pyright-langserver') then
  local lspconfig = require('lspconfig')
  lspconfig.pyright.setup{}
end