" ======================================================
" Base Vim Configuration
" ======================================================

" Core Settings
set nocompatible
set backspace=indent,eol,start
set history=1000
set showcmd
set showmode
set incsearch
set hlsearch
set number
set ruler
set wildmenu

" Indentation
set autoindent
set smartindent
set tabstop=4
set shiftwidth=4
set expandtab

" Interface improvements
syntax on
filetype plugin indent on
set cursorline
set laststatus=2
set statusline=%f\ %h%w%m%r\ %=%(%l,%c%V\ %=\ %P%)

" File management
set nobackup
set noswapfile
set autoread
set hidden

" Search behaviors
set ignorecase
set smartcase

" Performance
set ttyfast
set lazyredraw

" Common key remappings
nnoremap <Space> <Nop>
let mapleader = " "
nnoremap <leader>w :w<CR>
nnoremap <leader>q :q<CR>
nnoremap <leader>e :e $MYVIMRC<CR>
nnoremap <leader>s :source $MYVIMRC<CR>
nnoremap <C-h> :nohl<CR>

" Navigation improvements
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-h> <C-w>h
nnoremap <C-l> <C-w>l

" Sensible defaults
set encoding=utf-8
set scrolloff=3
set sidescrolloff=5
set display+=lastline
set linebreak
set clipboard=unnamed,unnamedplus

" Colors
set background=dark
if has('termguicolors')
  set termguicolors
endif

" Mouse
if has('mouse')
  set mouse=a
endif