""" Disable vi compatibility mode for improved features
""" Note: This is automatically set when a vimrc is found, but kept for clarity
set nocompatible

""" Enable syntax highlighting
syntax on

""" Enable filetype detection, plugins, and indentation
filetype plugin indent on

""" Set leader key to space for custom mappings
""" This makes it easier to create and use custom shortcuts
let mapleader = " "
let maplocalleader = ","

""" Map jk and kj to escape in insert mode
""" This provides alternative ways to exit insert mode without reaching for Esc
inoremap jk <Esc>
inoremap kj <Esc>

""" Allow backspacing over everything in insert mode
""" Makes backspace behave as expected in all contexts
set backspace=indent,eol,start

""" Set a reasonable history size
""" Increases the number of commands remembered
set history=1000

""" Enable hidden buffers
""" Allows switching buffers without saving, preserving changes
set hidden

""" Automatically read files when changed outside of Vim
""" Updates the buffer when a file is changed externally
set autoread

""" Use the system clipboard
""" Seamlessly copy/paste between Vim and other applications
set clipboard=unnamed

""" Set default encoding to UTF-8
""" Ensures proper handling of international characters
set encoding=utf-8

""" Enable mouse support in all modes
""" Allows using the mouse for selecting text, positioning cursor, etc.
set mouse=a

""" Set command-line completion mode
""" Enhances the command-line experience with better completion
set wildmenu
set wildmode=list:longest,full

""" Disable error bells
""" Eliminates annoying sounds when reaching buffer limits
set noerrorbells
set visualbell
set t_vb=

""" Set default file format preference order
""" Tries to use Unix format first, then DOS, then Mac
set fileformats=unix,dos,mac

""" Set timeout for key sequences
""" Makes key combinations more responsive
set timeout
set timeoutlen=1000
set ttimeoutlen=100
