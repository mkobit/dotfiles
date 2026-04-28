-- Search Settings
local opt = vim.opt

-- Enable incremental search - show matches while typing
opt.incsearch = true
-- Highlight all search matches
opt.hlsearch = true
-- Ignore case in search patterns
opt.ignorecase = true
-- Override ignorecase if search pattern contains uppercase
opt.smartcase = true

-- Clear search highlighting on <esc>
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>', { desc = 'Clear search highlighting' })
