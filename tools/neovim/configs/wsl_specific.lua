-- WSL-specific Neovim settings (Lua)

-- WSL clipboard integration
if vim.fn.has('wsl') == 1 then
  vim.g.clipboard = {
    name = 'wslclipboard',
    copy = {
      ['+'] = 'clip.exe',
      ['*'] = 'clip.exe',
    },
    paste = {
      ['+'] = 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
      ['*'] = 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
    },
    cache_enabled = 0,
  }
end

-- GUI Font settings for WSL
if vim.g.neovide then
  vim.o.guifont = "JetBrainsMono Nerd Font:h12"
end

-- Support for system commands
vim.opt.shell = "/bin/bash"

-- Path settings for both Windows and WSL
vim.opt.path:append("/usr/include/,/usr/local/include/,/mnt/c/Windows/System32/")

-- Open URLs in Windows browser from WSL
if vim.fn.has('wsl') == 1 then
  local open_url = function()
    local uri = vim.fn.expand('<cWORD>')
    uri = uri:gsub('?', '\\?')
    uri = vim.fn.shellescape(uri, true)
    vim.fn.system('cmd.exe /c start "" ' .. uri)
    vim.cmd('redraw!')
  end
  
  vim.keymap.set('n', '<leader>o', open_url, { noremap = true, silent = true, desc = "Open URL under cursor" })
end

-- External commands in WSL
if vim.fn.executable('rg') == 1 then
  vim.opt.grepprg = "rg --vimgrep --smart-case --follow"
end

-- WSL-specific directory detection
local function is_windows_path(path)
  return path:match('^/mnt/[a-z]') ~= nil
end

-- WSL-specific path conversion
local function to_windows_path(path)
  if is_windows_path(path) then
    local drive = path:sub(6, 6):upper()
    local rest = path:sub(8)
    return drive .. ":\\" .. rest:gsub('/', '\\')
  end
  return path
end

-- Function to check if a Windows executable exists in PATH
local function has_win_executable(cmd)
  local where_cmd = 'cmd.exe /c where ' .. cmd
  return vim.fn.system(where_cmd):match(cmd .. '.exe') ~= nil
end

-- WSL and Windows integration
if vim.fn.has('wsl') == 1 then
  -- Check for Windows tools that could be used
  if has_win_executable('pwsh') then
    -- PowerShell is available, could configure shell
    -- vim.opt.shell = 'pwsh.exe'
    -- vim.opt.shellcmdflag = '-command'
  end
  
  -- Windows-specific file associations
  vim.g.win_open_with = {
    ['.pdf'] = 'cmd.exe /c start ""',
    ['.docx'] = 'cmd.exe /c start ""',
    ['.xlsx'] = 'cmd.exe /c start ""',
  }
  
  -- Add helper function to open files with Windows apps
  vim.cmd [[
  function! OpenWithWindows()
    let file = expand('%:p')
    let ext = expand('%:e')
    if has_key(g:win_open_with, '.' . ext)
      call system(g:win_open_with['.' . ext] . ' ' . shellescape(file))
    else
      call system('cmd.exe /c start "" ' . shellescape(file))
    endif
  endfunction
  command! OpenWithWindows call OpenWithWindows()
  ]]
end