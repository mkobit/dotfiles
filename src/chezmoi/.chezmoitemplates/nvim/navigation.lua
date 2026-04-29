-- Navigation Settings
local opt = vim.opt
local keymap = vim.keymap

-- Keep a minimum number of lines visible above/below cursor
opt.scrolloff = 5
opt.sidescrolloff = 10

-- Make j and k navigate display lines rather than physical lines
keymap.set('n', 'j', 'gj', { desc = 'Move down display line' })
keymap.set('n', 'k', 'gk', { desc = 'Move up display line' })

-- Simple window navigation
keymap.set('n', '<M-h>', '<C-w>h', { desc = 'Move to left window' })
keymap.set('n', '<M-j>', '<C-w>j', { desc = 'Move to lower window' })
keymap.set('n', '<M-k>', '<C-w>k', { desc = 'Move to upper window' })
keymap.set('n', '<M-l>', '<C-w>l', { desc = 'Move to right window' })

-- Basic buffer navigation
keymap.set('n', '<Leader>bn', ':bnext<CR>', { desc = 'Next buffer', silent = true })
keymap.set('n', '<Leader>bp', ':bprevious<CR>', { desc = 'Previous buffer', silent = true })
keymap.set('n', '<Leader>bd', ':bdelete<CR>', { desc = 'Close buffer', silent = true })

-- Center screen when jumping to search results
keymap.set('n', 'n', 'nzz', { desc = 'Next search result' })
keymap.set('n', 'N', 'Nzz', { desc = 'Previous search result' })

-- Remember last location in file
vim.api.nvim_create_autocmd("BufReadPost", {
  group = vim.api.nvim_create_augroup("remember_position", { clear = true }),
  callback = function()
    local mark = vim.api.nvim_buf_get_mark(0, '"')
    local lcount = vim.api.nvim_buf_line_count(0)
    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})
