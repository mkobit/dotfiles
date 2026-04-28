-- Editing Settings
local opt = vim.opt
local keymap = vim.keymap

-- Enable persistent undo (maintain undo history between sessions)
opt.undofile = true
opt.undolevels = 1000
opt.undoreload = 10000

-- Don't create backup files
opt.backup = false
opt.writebackup = false
opt.swapfile = false

-- Use system clipboard for all operations
opt.clipboard = 'unnamedplus'

-- Set a reasonable update time (affects plugins like gitgutter)
opt.updatetime = 300

-- Show matching brackets when cursor is over them
opt.showmatch = true
opt.matchtime = 2

-- Enable spell checking but turn it off by default
opt.spelllang = 'en_us'
opt.spell = false
-- Toggle spell checking with F7
keymap.set('n', '<F7>', ':setlocal spell!<CR>', { desc = 'Toggle spell checking', silent = true })

-- Auto-complete settings
opt.completeopt = { 'menuone', 'noselect' }

-- Auto-save when focus is lost
vim.api.nvim_create_autocmd("FocusLost", {
  command = "silent! wall"
})

-- Automatically save when exiting insert mode
vim.api.nvim_create_autocmd("InsertLeave", {
  command = "silent! update"
})

-- Automatically strip trailing whitespace on save
vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = "*",
  command = "%s/\\s\\+$//e"
})

-- Enable word wrapping for text files
vim.api.nvim_create_autocmd("FileType", {
  pattern = { "text", "markdown", "html", "tex", "adoc" },
  command = "setlocal wrap linebreak nolist"
})

-- Automatically continue comments on new lines
opt.formatoptions:append('r')

-- Allow virtual editing in visual block mode
opt.virtualedit = 'block'

-- Make Y behave like D and C (yank to end of line)
keymap.set('n', 'Y', 'y$', { desc = 'Yank to end of line' })

-- Preserve selection when indenting in visual mode
keymap.set('v', '<', '<gv', { desc = 'Indent left and re-select' })
keymap.set('v', '>', '>gv', { desc = 'Indent right and re-select' })

-- Maintain cursor position when joining lines
keymap.set('n', 'J', 'mzJ`z', { desc = 'Join lines and keep cursor' })

-- Quickly insert an empty new line without entering insert mode
keymap.set('n', '<Leader>o', 'o<Esc>', { desc = 'Insert blank line below' })
keymap.set('n', '<Leader>O', 'O<Esc>', { desc = 'Insert blank line above' })

-- Quick save
keymap.set('n', '<Leader>w', ':w<CR>', { desc = 'Save file', silent = true })

-- Disable Ex mode (avoid accidental activation)
keymap.set('n', 'Q', '<nop>')

-- Automatically create directories when saving files
vim.api.nvim_create_autocmd("BufWritePre", {
  group = vim.api.nvim_create_augroup("BWCCreateDir", { clear = true }),
  callback = function(event)
    if event.match:match("^%w%w+:[\\/][\\/]") then
      return
    end
    local file = vim.loop.fs_realpath(event.match) or event.match
    vim.fn.mkdir(vim.fn.fnamemodify(file, ":p:h"), "p")
  end,
})
