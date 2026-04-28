-- UI Settings
local opt = vim.opt

-- Show line numbers on the left side
opt.number = true
-- Show relative line numbers
opt.relativenumber = true

-- Show cursor position in the bottom right
opt.ruler = true

-- Allow backspace to work as expected in insert mode
opt.backspace = { 'indent', 'eol', 'start' }

-- Show partial commands in the last line of the screen
opt.showcmd = true

-- Show matching brackets/parentheses when cursor is over them
opt.showmatch = true

-- Enhanced command-line completion
opt.wildmenu = true

-- Highlight the current line
opt.cursorline = true

-- Keep 3 lines visible above/below cursor when scrolling
opt.scrolloff = 3

-- Enable mouse support in all modes
opt.mouse = 'a'

-- Always show status line
opt.laststatus = 2

-- Use dark background colors
opt.background = 'dark'

-- Disable bells and visual bells
opt.errorbells = false
opt.visualbell = false
