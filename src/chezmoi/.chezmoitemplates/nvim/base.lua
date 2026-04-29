-- Base Settings
local opt = vim.opt

-- Set leader key to space for custom mappings
vim.g.mapleader = " "
vim.g.maplocalleader = ","

-- Map jk and kj to escape in insert mode
vim.keymap.set('i', 'jk', '<Esc>', { noremap = true })
vim.keymap.set('i', 'kj', '<Esc>', { noremap = true })

-- Set a reasonable history size
opt.history = 1000

-- Enable hidden buffers
opt.hidden = true

-- Automatically read files when changed outside of Vim
opt.autoread = true

-- Use the system clipboard
opt.clipboard = 'unnamedplus'

-- Set default encoding to UTF-8
opt.encoding = 'utf-8'

-- Set default file format preference order
opt.fileformats = { 'unix', 'dos', 'mac' }

-- Set timeout for key sequences
opt.timeout = true
opt.timeoutlen = 1000
opt.ttimeoutlen = 100
