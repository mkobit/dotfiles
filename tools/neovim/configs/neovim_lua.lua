-- Neovim Lua Configuration
-- This file contains settings for Neovim using Lua syntax

-- Helper function to check if a file exists
local function file_exists(file)
  local f = io.open(file, "r")
  if f ~= nil then
    io.close(f)
    return true
  else
    return false
  end
end

-- Basic Settings (Lua equivalents)
vim.g.mapleader = " "
vim.g.maplocalleader = ","

-- UI and Visual Settings
vim.opt.termguicolors = true
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.cursorline = true
vim.opt.signcolumn = "yes"
vim.opt.showmode = true
vim.opt.laststatus = 3  -- Global statusline (Neovim 0.7+)
vim.opt.title = true
vim.opt.cmdheight = 1

-- Tabs and Indents
vim.opt.expandtab = true
vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.softtabstop = 2
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.breakindent = true

-- Search settings
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.hlsearch = true
vim.opt.incsearch = true

-- Split behavior
vim.opt.splitbelow = true
vim.opt.splitright = true

-- File handling
vim.opt.backup = false
vim.opt.writebackup = false
vim.opt.swapfile = false
vim.opt.undofile = true
vim.opt.undodir = vim.fn.stdpath("data") .. "/undo"

-- Text display
vim.opt.wrap = true
vim.opt.linebreak = true
vim.opt.list = true
vim.opt.listchars = {
  tab = "→ ", 
  trail = "·",
  extends = "»",
  precedes = "«",
  nbsp = "×"
}

-- Performance and behavior
vim.opt.updatetime = 300
vim.opt.timeoutlen = 500
vim.opt.scrolloff = 8
vim.opt.sidescrolloff = 8
vim.opt.mouse = "a"
vim.opt.clipboard = "unnamedplus"
vim.opt.completeopt = "menuone,noselect"
vim.opt.inccommand = "split"

-- Global status line
vim.opt.laststatus = 3

-- Key mappings (Lua style)
local function map(mode, lhs, rhs, opts)
  local options = { noremap = true, silent = true }
  if opts then
    options = vim.tbl_extend("force", options, opts)
  end
  vim.keymap.set(mode, lhs, rhs, options)
end

-- Clear search highlighting
map("n", "<Esc><Esc>", ":nohlsearch<CR>")

-- Window navigation
map("n", "<C-h>", "<C-w>h")
map("n", "<C-j>", "<C-w>j")
map("n", "<C-k>", "<C-w>k")
map("n", "<C-l>", "<C-w>l")

-- Buffer navigation
map("n", "<leader>bn", ":bnext<CR>")
map("n", "<leader>bp", ":bprevious<CR>")
map("n", "<leader>bd", ":bdelete<CR>")

-- File explorer
map("n", "<leader>e", ":Explore<CR>")

-- Source Vim config
map("n", "<leader>sv", ":source $MYVIMRC<CR>")

-- Quick save
map("n", "<leader>w", ":write<CR>")

-- Terminal
map("n", "<leader>t", ":terminal<CR>")
map("t", "<Esc>", "<C-\\><C-n>")

-- Setup Plugins (using lazy.nvim)
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Plugin Configuration
require("lazy").setup({
  -- Core plugins
  { "nvim-lua/plenary.nvim" },
  
  -- UI enhancements
  { "folke/tokyonight.nvim", priority = 1000, config = function()
    vim.cmd.colorscheme("tokyonight-night")
  end },
  { "nvim-lualine/lualine.nvim", 
    config = function()
      require('lualine').setup({
        options = {
          theme = 'tokyonight',
          section_separators = '',
          component_separators = '|'
        }
      })
    end 
  },
  
  -- File navigation
  { "nvim-telescope/telescope.nvim", 
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
      local telescope = require('telescope')
      telescope.setup({
        defaults = {
          file_ignore_patterns = { "node_modules", ".git" }
        }
      })
      
      -- Telescope mappings
      map("n", "<leader>ff", ":Telescope find_files<CR>")
      map("n", "<leader>fg", ":Telescope live_grep<CR>")
      map("n", "<leader>fb", ":Telescope buffers<CR>")
      map("n", "<leader>fh", ":Telescope help_tags<CR>")
    end
  },
  
  -- Editor enhancements
  { "nvim-treesitter/nvim-treesitter", 
    build = ":TSUpdate",
    config = function()
      require('nvim-treesitter.configs').setup({
        ensure_installed = { 
          "lua", "vim", "vimdoc", "bash", "python", "javascript", 
          "typescript", "json", "yaml", "go", "rust"
        },
        highlight = { enable = true },
        indent = { enable = true }
      })
    end
  },
  
  -- IDE features
  { "neovim/nvim-lspconfig",
    dependencies = {
      "hrsh7th/nvim-cmp",
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
      "saadparwaiz1/cmp_luasnip",
      "L3MON4D3/LuaSnip",
    },
    config = function()
      -- LSP configuration would go here
      local lspconfig = require('lspconfig')
      
      -- Setup common LSP servers
      local servers = { 'pyright', 'tsserver', 'gopls', 'rust_analyzer' }
      for _, lsp in ipairs(servers) do
        lspconfig[lsp].setup {}
      end
      
      -- LSP key mappings
      map("n", "gd", vim.lsp.buf.definition)
      map("n", "gr", vim.lsp.buf.references)
      map("n", "K", vim.lsp.buf.hover)
      map("n", "<leader>rn", vim.lsp.buf.rename)
      map("n", "<leader>ca", vim.lsp.buf.code_action)
    end
  },
})

-- Color scheme
vim.cmd.colorscheme("tokyonight-night")

-- Load local Lua customizations if they exist
local local_lua_path = vim.fn.stdpath("config") .. "/local.lua"
if file_exists(local_lua_path) then
  dofile(local_lua_path)
end