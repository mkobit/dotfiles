" Neovim Base Configuration (VimL)
" This file contains base settings for Neovim using VimL syntax

" Leader keys
let mapleader = " "
let maplocalleader = ","

" Basic Settings
set nocompatible
set encoding=utf-8
set fileencoding=utf-8
set termguicolors
set number
set relativenumber
set ignorecase
set smartcase
set mouse=a
set clipboard=unnamedplus
set inccommand=split
set completeopt=menuone,noselect

" Tabs and Indents
set expandtab
set tabstop=2
set shiftwidth=2
set softtabstop=2
set autoindent
set smartindent
set breakindent

" Search settings
set incsearch
set hlsearch

" Editor appearance
set cursorline
set signcolumn=yes
set splitbelow
set splitright
set cmdheight=1
set showmode
set laststatus=3  " Global statusline in Neovim 0.7+
set title

" General workflows
set hidden
set nobackup
set nowritebackup
set noswapfile
set undofile
set undodir=~/.local/share/nvim/undo
set updatetime=300
set timeoutlen=500
set scrolloff=8
set sidescrolloff=8
set wrap
set linebreak
set list
set listchars=tab:→\ ,trail:·,extends:»,precedes:«,nbsp:×

" File type detection and syntax
filetype plugin indent on
syntax enable

" Key Mappings
" Clear search highlighting
nnoremap <silent> <Esc><Esc> :nohlsearch<CR>

" Window navigation
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" Buffer navigation
nnoremap <leader>bn :bnext<CR>
nnoremap <leader>bp :bprevious<CR>
nnoremap <leader>bd :bdelete<CR>

" File explorer
nnoremap <leader>e :Explore<CR>

" Source Vim config
nnoremap <leader>sv :source $MYVIMRC<CR>

" Quick save
nnoremap <leader>w :write<CR>

" Terminal
nnoremap <leader>t :terminal<CR>
tnoremap <Esc> <C-\><C-n>

" Allow local customizations
if filereadable(expand("~/.config/nvim/local.vim"))
  source ~/.config/nvim/local.vim
endif